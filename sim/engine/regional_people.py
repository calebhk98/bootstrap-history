"""Where the nation's people live, region by region (Complaint 603).

A region is a tile the nation holds. Each year every region is fed the food its own households ate (the economy's
tile accounts, kept by `record_food_eaten`), steps by the same `Population.step` as the nation, and sends some of its
working-age people to a bordering region where people ate better, by the labour market's migration rule. The nation's
`Population` is the sum of the regions.
"""
from typing import Dict, List, Mapping, Tuple

from sim.geography.api import settlement
from sim.labour.api import migration_shares
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR
from sim.world import regional_population
from sim.world.demography import Population
from sim.world.military_logistics import ARMY_MARCH_RATE_KM_PER_DAY


def moves_between_regions(regions: Mapping[str, Population], eaten_over_need: Mapping[str, float],
                          borders: Mapping[str, List[str]], distance_km) -> Tuple[Dict[str, float], Dict[str, float]]:
    """({region: working-age people leaving}, {region: arriving}) this year. Where people ate better is the
    destination's real income over its subsistence; a day on the road costs a day of the origin's subsistence."""
    leaving: Dict[str, float] = {}
    arriving: Dict[str, float] = {}
    for origin in sorted(regions):
        real_origin = eaten_over_need.get(origin, 0.0)
        working_age = regions[origin].working_age
        if real_origin <= 0.0 or working_age <= 0.0:
            continue
        destinations = [tile for tile in sorted(borders.get(origin, ())) if tile in regions]
        options = [(eaten_over_need.get(tile), distance_km(origin, tile) / ARMY_MARCH_RATE_KM_PER_DAY / CIVIL_DAYS_PER_YEAR)
                   for tile in destinations]
        for destination, share in zip(destinations, migration_shares(real_origin, options)):
            if share > 0.0:
                moved = working_age * share
                leaving[origin] = leaving.get(origin, 0.0) + moved
                arriving[destination] = arriving.get(destination, 0.0) + moved
    return leaving, arriving


class RegionalPeopleMixin:

    def regions_of_people(self) -> Dict[str, Population]:
        """The regions, kept to the nation: the tiles held, summing to `self.population`."""
        homes = self.home_tiles_held()
        tiles = settlement.tile_ids(homes)
        regions = regional_population.to_populations(self.state.population.regions)
        regional_population.keep_to_nation(
            regions, self.population, tiles, {tile: settlement.population_share(homes, tile) for tile in tiles})
        return regions

    def people_by_tile(self):
        """{tile: people} once the regions cover the tiles held, else None (the caller spreads the nation by share)."""
        stored = self.state.population.regions
        if not stored or sorted(stored) != settlement.tile_ids(self.home_tiles_held()):
            return None
        held = sum(sum(bands) for bands in stored.values())
        scale = self.population.total / held if held > 0.0 else 0.0
        return {tile: sum(bands) * scale for tile, bands in stored.items()}

    def regional_kcal_per_day(self, regions, farm_kcal_per_day):
        """{region: calories a day it is fed}: its households' eaten over need where the economy has booked it, else
        the nation's, else its share of the farm model's harvest; open works' relief is shared by need."""
        state = self.state.population
        need = {tile: regional_population.adult_equivalents(region) for tile, region in regions.items()}
        total_need = sum(need.values())
        relief = self.relief_kcal_per_day()
        fed = {}
        for tile, region in regions.items():
            ratio = state.regional_eaten_over_need.get(tile, state.food_eaten_over_need)
            share = need[tile] / total_need if total_need > 0.0 else 0.0
            base = (regional_population.kcal_per_day_fed(region, ratio) if ratio is not None
                    else farm_kcal_per_day * share)
            fed[tile] = base + relief * share
        return fed

    def step_regions_of_people(self, regions, kcal_by_region, year):
        """Step every region a year and return the nation's flows; the nation's `Population` becomes their sum."""
        borders = {tile: self.world_map.tiles[tile]["borders"] for tile in regions if tile in self.world_map.tiles}
        leaving, arriving = moves_between_regions(
            regions, self.state.population.regional_eaten_over_need, borders, settlement.distance_between_tiles_km)
        food = sum(kcal_by_region.values())
        epidemic_deaths = self.disease_year(food, year)
        self.epidemic_hits_seats(epidemic_deaths, year)
        ratio = self.population.nutrition_ratio(food)
        flows = regional_population.step_regions(
            regions, kcal_by_region, self._disease_burden(), epidemic_deaths, self.endemic_death_rates(), leaving, arriving)
        for band in regional_population.BANDS:
            setattr(self.population, band, sum(getattr(region, band) for region in regions.values()))
        self.state.population.regions = regional_population.to_stored(regions)
        self._last_regional_step = flows
        return regional_population.national_flows(flows, ratio)
