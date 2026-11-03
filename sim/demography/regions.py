"""Where the nation's people live, region by region, and what they ate (Complaint 603).

A region is a tile the nation holds. Each year every region is fed the food its own households ate (the economy's tile
accounts, kept by `record_food_eaten`), steps by the same `Population.step` as the nation, and sends some of its working-age
people to a bordering region where people ate better, by the labour market's migration rule. The nation's people are the sum
of the regions.

The economy books food eaten per cohort (`sim/economy/year_accounts.py`). The nation's people-weighted eaten over need is kept
when the economy's year closes, and the next year's step turns it into the calories a day it is fed. While no economy year
has closed (a game just opened, or a game whose economy never ran) the opening's basket feeds each region its full need."""
from typing import Dict

from sim.actors.api import RecordMigrantContact
from sim.assembly.api import Part
from sim.disease.api import HitSeatsWithEpidemic, RunEpidemicYear
from sim.geography.api import settlement
from sim.labour.api import migrant_pairs, totals_of_pairs
from sim.world import regional_population
from sim.world.demography import Population

from . import moves, rules


class Regions(Part):

    def __init__(self, module):
        super().__init__(module)
        self._last_demographic_step = None     # the nation's flows of the last yearly step, until the next
        self._last_regional_step = None        # the same by region

    def _regions(self) -> Dict[str, Population]:
        """The regions, kept to the nation: the tiles held, summing to the nation's people."""
        shares = settlement.population_shares(self.needs.home_tiles_held())
        regions = regional_population.to_populations(self.world.regions)
        regional_population.keep_to_nation(regions, self.parts.counts._bands(), list(shares), shares)
        return regions

    def people_by_tile(self):
        """{tile: people} once the regions cover the tiles held, else None (the caller spreads the nation by share)."""
        return settlement.people_by_tile(self.world.regions, self.parts.counts._bands().total, self.needs.home_tiles_held())

    def regional_people_by_band(self):
        """{tile: (children, working_age, elderly)} the regions the module tracks (empty until they are first kept), as a copy."""
        return {tile: tuple(bands) for tile, bands in self.world.regions.items()}

    def food_eaten(self):
        """{tile: share of the people's food need the tile's people ate}."""
        return self.world.regional_eaten_over_need

    def demographic_flows(self):
        """The nation's flows of the last yearly step (births, deaths, nutrition ratio), None before the first."""
        return self._last_demographic_step

    def nutrition_ratio_last_year(self):
        """The share of the people's food need the last year's supply met, or None before a year has been stepped."""
        return rules.nutrition_ratio_of(self._last_demographic_step)

    def regional_flows_last_year(self):
        """{tile: flows} of the last yearly step by region, None before the first."""
        return self._last_regional_step

    def record_food_eaten(self, command):
        """Keep the year's national and regional food eaten over need, for the next yearly step."""
        self.world.food_eaten_over_need = command.national
        self.world.regional_eaten_over_need = dict(command.by_tile)

    def move_people(self, command):
        """Keep the labour market's moves of the year (net working-age people by tile) for the next yearly step."""
        for tile, change in command.net_by_tile.items():
            self.world.moves_asked[tile] = self.world.moves_asked.get(tile, 0.0) + change

    def _regional_kcal_per_day(self, regions):
        """{region: calories a day it is fed}: its own households' eaten over need where the economy has booked it, else
        the opening's full ration; open works' relief is shared by need."""
        return regional_population.kcal_per_day_by_region(
            regions, self.world.regional_eaten_over_need, self.needs.relief_kcal_per_day())

    def externality_deaths(self, deaths_by_band, year):
        """`deaths_by_band` plus what the game's externality providers add to the year's deaths."""
        return rules.deaths_with_externalities(deaths_by_band, self.needs.externality(year))

    def _step_regions(self, regions, kcal_by_region, year):
        """Step every region a year and return the nation's flows; the nation's people become their sum."""
        borders = self.needs.borders_among(list(regions))
        pairs = migrant_pairs(regions, self.world.regional_eaten_over_need, borders, settlement.distance_between_tiles_km)
        pairs = moves.within_working_age(pairs + moves.pairs_of_net_moves(self.world.moves_asked, regions), regions)   # one rule: food and wage moves together
        self.world.moves_asked = {}
        self.needs.send(RecordMigrantContact(tuple(pairs)))
        leaving, arriving = totals_of_pairs(pairs)
        food = sum(kcal_by_region.values())
        deaths = self.externality_deaths(self.needs.send(RunEpidemicYear(food, year)), year)
        self.needs.send(HitSeatsWithEpidemic(deaths, year))
        burden, endemic_death_rates = self.needs.disease_burden(), self.needs.endemic_death_rates()
        ratio = self.parts.counts._bands().nutrition_ratio(food)
        flows = regional_population.step_regions(
            regions, kcal_by_region, burden, deaths, endemic_death_rates, leaving, arriving,
            self.needs.town_mortality_premium_by_tile(), epidemic_deaths_by_tile=self.needs.epidemic_deaths_by_tile() or None)
        self.parts.counts._store(*(sum(getattr(region, band) for region in regions.values()) for band in regional_population.BANDS))
        self.world.regions = regional_population.to_stored(regions)
        self._last_regional_step = flows
        return regional_population.national_flows(flows, ratio)
