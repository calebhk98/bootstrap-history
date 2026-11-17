"""The opening holds a producer to the runs its granted land allows, and the users of what it makes to that supply:
`opening_land_fit.held_to_land`, `limited_goods` with the land a run takes, and `fit_to_land`. Stub setup and hand-built
producers; no game."""
import types
import unittest

from sim.economy import opening_land_fit, opening_runs
from sim.economy.producers import Producer
from sim.economy.record import EconomyRecord
from sim.economy.types import Recipe

QUICK_TOPIC = True


class HeldToLandTests(unittest.TestCase):
    def test_sales_and_plant_are_cut_to_the_runs_the_land_allows(self):
        self.assertEqual(opening_land_fit.held_to_land(100.0, 150.0, 40.0), (40.0, 60.0))

    def test_a_producer_with_no_land_limit_is_left_as_it_is(self):
        self.assertEqual(opening_land_fit.held_to_land(100.0, 150.0, None), (100.0, 150.0))

    def test_land_enough_for_its_sales_changes_nothing(self):
        self.assertEqual(opening_land_fit.held_to_land(100.0, 150.0, 100.0), (100.0, 150.0))


class LandBoundGoodsTests(unittest.TestCase):
    def setUp(self):
        self.recipes = {
            "fell": Recipe("fell", {"timber": 1.0}, {}, {"labourer": 1.0}),
            "burn": Recipe("burn", {"fuel": 1.0}, {"timber": 1.0}, {"labourer": 1.0}),
            "weave": Recipe("weave", {"cloth": 1.0}, {}, {"weaver": 1.0}),
        }

    def test_what_only_land_makes_is_limited_and_so_is_what_is_made_from_it(self):
        limited = opening_runs.limited_goods(self.recipes, {}, {"fell": 2.0})
        self.assertEqual(limited, {"timber", "fuel"})

    def test_without_the_land_figures_only_deposits_limit_a_good(self):
        self.assertEqual(opening_runs.limited_goods(self.recipes, {}), set())


class FitToLandTests(unittest.TestCase):
    """A wood whose land allows a quarter of the felling the opening sized, and a kiln that burns its timber."""

    def setUp(self):
        recipes = {
            "fell": Recipe("fell", {"timber": 1.0}, {}, {"labourer": 1.0}),
            "burn": Recipe("burn", {"fuel": 1.0}, {"timber": 1.0}, {"labourer": 1.0}),
        }
        self.setup = types.SimpleNamespace(recipes=recipes, site_limits=(), land_per_run={"fell": 2.0})
        self.record = EconomyRecord.__new__(EconomyRecord)
        self.record.producers = {
            "producer:fell@tile": Producer("producer:fell@tile", "owner", "fell", "tile", 600.0, expected_sales=400.0,
                                           land_run_cap=100.0),
            "producer:burn@tile": Producer("producer:burn@tile", "owner", "burn", "tile", 800.0, expected_sales=400.0),
        }

    def test_the_fellers_are_held_to_their_land_and_the_burners_to_the_timber_left(self):
        opening_land_fit.fit_to_land(self.setup, self.record)
        feller, burner = self.record.producers["producer:fell@tile"], self.record.producers["producer:burn@tile"]
        self.assertAlmostEqual(feller.expected_sales, 100.0)
        self.assertAlmostEqual(feller.capacity_runs, 150.0)
        self.assertAlmostEqual(burner.expected_sales, 100.0)
        self.assertAlmostEqual(burner.capacity_runs, 200.0)


if __name__ == "__main__":
    unittest.main()
