"""Complaint 640: the seam between the economy's food and the people. The demography module's `step_population` feeds the
regions what their households ate, steps them, records the year's flows and advances the colonies."""
QUICK_TOPIC = True

import types
import unittest

from sim.demography.api import StepPopulation
from sim.demography.constants import YEARLY_RECORD_LIMIT
from sim.demography.module import Demography
from sim.demography.state import DemographyWorld
from sim.land.api import AdvanceColonies
from sim.tests import module_harness


class Stepped(Demography):
    """The module with the regions' feeding and stepping stood in: the seam under test is the yearly step's."""

    def _regions(self):
        return {"north": object(), "south": object()}

    def _regional_kcal_per_day(self, regions):
        return {name: 2000.0 for name in regions}

    def _step_regions(self, regions, kcal_by_region, year):
        self.fed.append(dict(kcal_by_region))
        return types.SimpleNamespace(births=10.2, deaths=4.7, nutrition_ratio=0.98765)


def built():
    views = {}
    world = DemographyWorld(pop_children=300.0, pop_working_age=600.0, pop_elderly=100.0)
    module = module_harness.build(Stepped, views=views, world=world)
    module.fed = []
    return module


class DemographicRecovery(unittest.TestCase):
    def test_the_regions_are_fed_what_the_step_hands_them(self):
        module = built()
        module.step_population(StepPopulation(101))
        self.assertEqual(module.fed, [{"north": 2000.0, "south": 2000.0}])

    def test_the_colonies_advance_after_the_step(self):
        module = built()
        module.step_population(StepPopulation(107))
        sent = module_harness.sent(module)
        self.assertEqual(sent[-1], AdvanceColonies(107))

    def test_the_years_flows_are_recorded_and_only_the_latest_are_kept(self):
        module = built()
        for year in range(100, 100 + YEARLY_RECORD_LIMIT + 5):
            module.step_population(StepPopulation(year))
        record = module.world.yearly_record
        self.assertEqual(len(record), YEARLY_RECORD_LIMIT)
        self.assertEqual(record[-1], {"year": 100 + YEARLY_RECORD_LIMIT + 4, "population": 1000.0, "births": 10,
                                      "deaths": 5, "nutrition_ratio": 0.9877})


if __name__ == "__main__":
    unittest.main()
