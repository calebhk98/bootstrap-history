"""Complaint 549: demography is fed what the agent economy's households ate, not the engine's own harvest.

The economy half (the national figure) is test_national_food_eaten_rule. This half books the figure in the demography module (the
command the engine's forwarder builds from the economy's outcome) and hands it to the regions; a region fed its own booked figure is
test_regional_hunger_is_the_regions_own."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.demography import regions
from sim.demography.api import RecordFoodEaten
from sim.demography.module import Demography
from sim.demography.state import DemographyWorld
from sim.engine.forward_demography import ForwardDemographyMixin
from sim.tests import module_harness
from sim.tests.test_national_food_eaten_rule import _accounts


def booked(outcome):
    """The command the engine's forwarder sends for the economy's `outcome`."""
    sent = []
    ForwardDemographyMixin.record_food_eaten(SimpleNamespace(send=sent.append), outcome)
    return sent[0]


class BookingTheFigure(unittest.TestCase):
    def test_the_economys_year_books_the_national_and_each_tiles_figure(self):
        command = booked(SimpleNamespace(accounts=_accounts({"town": 90.0, "farms": 100.0})))
        module = module_harness.build(Demography, world=DemographyWorld())
        module.record_food_eaten(command)
        self.assertAlmostEqual(module.world.food_eaten_over_need, 0.95, places=9)
        self.assertEqual(module.world.regional_eaten_over_need, {"town": 0.9, "farms": 1.0})

    def test_an_outcome_without_accounts_books_nothing(self):
        command = booked(SimpleNamespace())
        self.assertEqual(command, RecordFoodEaten(None, {}))
        module = module_harness.build(Demography, world=DemographyWorld(food_eaten_over_need=0.8, regional_eaten_over_need={"town": 0.8}))
        module.record_food_eaten(command)
        self.assertIsNone(module.world.food_eaten_over_need)
        self.assertEqual(module.world.regional_eaten_over_need, {})

    def test_the_view_answers_each_tiles_booked_figure(self):
        module = module_harness.build(Demography, world=DemographyWorld(regional_eaten_over_need={"town": 0.6}))
        self.assertEqual(module.food_eaten(), {"town": 0.6})


class ReadingTheFigure(unittest.TestCase):
    def test_each_region_is_fed_from_its_booked_figure_with_the_harvest_as_the_fallback(self):
        module = module_harness.build(Demography, views={"relief_kcal_per_day": 7.0, "home_tiles_held": ["town", "farms"]},
                                      world=DemographyWorld(regional_eaten_over_need={"town": 0.6}))
        recorded = []
        with mock.patch.object(regions.regional_population, "kcal_per_day_by_region",
                               lambda *arguments: recorded.append(arguments) or {"town": 1.0}), \
                mock.patch.object(regions.settlement, "population_shares", lambda tiles: {tile: 0.5 for tile in tiles}):
            fed = module._regional_kcal_per_day({"town": "region"}, 4000.0)
        self.assertEqual(fed, {"town": 1.0})
        self.assertEqual(recorded, [({"town": "region"}, {"town": 0.6}, 4000.0, 7.0, {"town": 0.5, "farms": 0.5})])


if __name__ == "__main__":
    unittest.main()
