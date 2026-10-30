"""Complaint 640: the seam between the farm model and the people. A year's harvest comes from land, labour and weather
(`farm_year.run_farm_year` on built inputs): lost farmland leaves a shortfall the same land does not. The demography module's
`step_population` hands that year's calories to the regions' step, carries the granary stock, records the harvest and the year's flows.
The storage and the population rules are in test_agriculture, test_granary_persistence and test_demography."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.demography import recovery
from sim.demography.api import People, StepPopulation, rules
from sim.demography.constants import YEARLY_RECORD_LIMIT
from sim.demography.module import Demography
from sim.demography.state import DemographySeat, DemographyWorld
from sim.land.api import AdvanceColonies
from sim.tests import module_harness
from sim.workforce.api import AllocateFarmWorkforce, ApplyLandClearing, UpdateWages
from sim.world import agriculture, farm_year as farm_year_model, farming_technique

POPULATION = 500000.0


def farm_year_of(land_share, weather=1.0, stock=0.0):
    land = agriculture.farmland_for_population(POPULATION)
    worked = agriculture.Land(land.hectares * land_share, quality=land.quality)
    workers = agriculture.farm_workers_fte_for_population(POPULATION)
    return farm_year_model.run_farm_year(worked, farming_technique.DEFAULT_TECHNIQUE, stock, POPULATION, workers, 42, weather)


class HarvestFromLand(unittest.TestCase):
    def test_land_sized_for_the_people_at_average_weather_leaves_no_shortfall(self):
        self.assertEqual(farm_year_of(1.0).farm_year.food_shortfall_kg, 0.0)

    def test_the_same_year_after_most_of_the_land_is_lost_leaves_a_shortfall_and_less_food_a_day(self):
        control, lost = farm_year_of(1.0).farm_year, farm_year_of(0.15).farm_year
        self.assertGreater(lost.food_shortfall_kg, 0.0)
        self.assertLess(lost.food_available_kcal_per_day, control.food_available_kcal_per_day)
        self.assertLess(lost.gross_harvest_kg, control.gross_harvest_kg)

    def test_a_worse_harvest_leaves_less_food_available(self):
        good, bad = farm_year_of(1.0, weather=1.2).farm_year, farm_year_of(1.0, weather=0.4).farm_year
        self.assertLess(bad.food_available_kcal_per_day, good.food_available_kcal_per_day)


FARM_LAND = object()


class Stepped(Demography):
    """The module with the regions' feeding and stepping stood in: the seam under test is the farm year's."""

    def _regions(self):
        return {"north": object(), "south": object()}

    def _regional_kcal_per_day(self, regions, farm_kcal_per_day):
        return {name: farm_kcal_per_day / len(regions) for name in regions}

    def _step_regions(self, regions, kcal_by_region, year):
        self.fed.append(dict(kcal_by_region))
        return types.SimpleNamespace(births=10.2, deaths=4.7, nutrition_ratio=0.98765)


def built(stock=123.0):
    views = {"weather_seed": lambda year, region: year, "harvest_weather": lambda year, stdev, harmed: 1.0,
             "farm_land": FARM_LAND, "farm_technique_this_year": farming_technique.DEFAULT_TECHNIQUE,
             "wage_index": 1.0, "wage_index_terms": {"base": 1.0, "elasticity": 0.5}}
    world = DemographyWorld(pop_children=300.0, pop_working_age=600.0, pop_elderly=100.0)
    module = module_harness.build(Stepped, views=views, answers={AllocateFarmWorkforce: 7.0}, world=world,
                                  seat=DemographySeat(farm_stock_kg=stock))
    module.fed = []
    return module


class DemographicRecovery(unittest.TestCase):
    def _run(self, module, year=101, stock_after=55.0, kcal=4000.0):
        farm_year = types.SimpleNamespace(food_available_kcal_per_day=kcal, food_shortfall_kg=3.0, gross_harvest_kg=900.0,
                                          marginal_product_last_hour_kg_per_hour=0.25)
        calls = []

        def run(*args):
            calls.append(args)
            return farm_year_model.FarmYear(farm_year, stock_after)
        with mock.patch.object(recovery.farm_year_model, "run_farm_year", run):
            module.step_population(StepPopulation(year))
        return calls, farm_year

    def test_the_years_harvest_calories_are_what_the_regions_are_fed(self):
        module = built()
        self._run(module, kcal=4000.0)
        self.assertEqual(module.fed, [{"north": 2000.0, "south": 2000.0}])

    def test_the_farm_year_is_run_on_the_land_the_workers_and_the_stock_carried(self):
        module = built()
        calls, _farm_year = self._run(module, year=105)
        land, technique, stock, people, workers, seed, weather = calls[0]
        self.assertIs(land, FARM_LAND)
        self.assertEqual((stock, people, workers, seed, weather), (123.0, rules.adult_equivalents(People(300.0, 600.0, 100.0)), 7.0, 105, 1.0))

    def test_the_stock_left_is_carried_to_the_next_year(self):
        module = built()
        self._run(module, stock_after=55.0)
        self.assertEqual(module.seat.farm_stock_kg, 55.0)

    def test_the_harvest_is_kept_for_the_screens(self):
        module = built()
        self._run(module)
        seat = module.seat
        self.assertEqual((seat.farm_last_shortfall_kg, seat.farm_last_harvest_kg), (3.0, 900.0))
        self.assertEqual(seat.farm_last_marginal_product, 0.25)

    def test_the_farm_workforce_land_and_wages_move_in_the_years_order(self):
        module = built()
        self._run(module, year=107)
        sent = module_harness.sent(module)
        self.assertEqual([type(command) for command in sent], [AllocateFarmWorkforce, ApplyLandClearing, UpdateWages, AdvanceColonies])
        self.assertEqual(sent[-1], AdvanceColonies(107))

    def test_the_years_flows_are_recorded_and_only_the_latest_are_kept(self):
        module = built()
        for year in range(100, 100 + YEARLY_RECORD_LIMIT + 5):
            self._run(module, year=year)
        record = module.world.yearly_record
        self.assertEqual(len(record), YEARLY_RECORD_LIMIT)
        self.assertEqual(record[-1], {"year": 100 + YEARLY_RECORD_LIMIT + 4, "population": 1000.0, "births": 10,
                                      "deaths": 5, "nutrition_ratio": 0.9877})


if __name__ == "__main__":
    unittest.main()
