"""Where the nation's people live, region by region (Complaint 603).

A region is a tile the nation holds. Each year every region is fed the food its own households ate (the economy's
tile accounts, kept by `record_food_eaten`), steps by the same `Population.step` as the nation, and sends some of its
working-age people to a bordering region where people ate better, by the labour market's migration rule. The nation's
`Population` is the sum of the regions.
"""
from typing import Dict

from sim.geography.api import settlement
from sim.labour.api import migrant_pairs, totals_of_pairs
from sim.world import regional_population
from sim.world.demography import Population

from . import contact_events


class RegionalPeopleMixin:

    def regions_of_people(self) -> Dict[str, Population]:
        """The regions, kept to the nation: the tiles held, summing to `self.population`."""
        shares = settlement.population_shares(self.home_tiles_held())
        regions = regional_population.to_populations(self.state.population.regions)
        regional_population.keep_to_nation(regions, self.population, list(shares), shares)
        return regions

    def people_by_tile(self):
        """{tile: people} once the regions cover the tiles held, else None (the caller spreads the nation by share)."""
        return settlement.people_by_tile(self.state.population.regions, self.population.total, self.home_tiles_held())

    def regional_kcal_per_day(self, regions, farm_kcal_per_day):
        """{region: calories a day it is fed}: its own households' eaten over need where the economy has booked it, else
        its land's share of the farm model's harvest; open works' relief is shared by need."""
        return regional_population.kcal_per_day_by_region(
            regions, self.state.population.regional_eaten_over_need, farm_kcal_per_day, self.relief_kcal_per_day(),
            settlement.population_shares(self.home_tiles_held()))

    def step_regions_of_people(self, regions, kcal_by_region, year):
        """Step every region a year and return the nation's flows; the nation's `Population` becomes their sum."""
        borders = self.geography.borders_among(list(regions))
        pairs = migrant_pairs(regions, self.state.population.regional_eaten_over_need, borders,
                              settlement.distance_between_tiles_km)
        contact_events.after_migration(self, pairs)
        leaving, arriving = totals_of_pairs(pairs)
        food = sum(kcal_by_region.values())
        epidemic_deaths, disease_burden, endemic_death_rates = self.epidemic_year(food, year)
        ratio = self.population.nutrition_ratio(food)
        flows = regional_population.step_regions(
            regions, kcal_by_region, disease_burden, epidemic_deaths, endemic_death_rates, leaving, arriving,
            self.labour.town_mortality_premium_by_tile())
        for band in regional_population.BANDS:
            setattr(self.population, band, sum(getattr(region, band) for region in regions.values()))
        self.state.population.regions = regional_population.to_stored(regions)
        self._last_regional_step = flows
        return regional_population.national_flows(flows, ratio)
