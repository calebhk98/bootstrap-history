"""A forest of limited yield, a kiln that burns its timber and a smelter that burns the kiln's fuel: `fit_to_supply` holds
each burner to what the producers upstream make. Stub setup and hand-built producers; no game."""
import types
import unittest

from sim.economy import opening_runs
from sim.economy.producers import Producer
from sim.economy.record import EconomyRecord
from sim.economy.types import Recipe, SiteLimit

QUICK_TOPIC = True

TOLERANCE = 1e-6      # share of the demand the float sums may miss by


def flows(setup, record):
    """({good: output of the producers at their expected sales}, {good: inputs they take at those sales})."""
    made, taken = {}, {}
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        for good, quantity in recipe.outputs.items():
            made[good] = made.get(good, 0.0) + quantity * producer.expected_sales * producer.yield_factor
        for good, quantity in recipe.inputs.items():
            taken[good] = taken.get(good, 0.0) + quantity * producer.expected_sales
    return made, taken


class FitToSupplyChainTests(unittest.TestCase):
    """A forest of limited yield, a kiln that burns its timber to fuel, a smelter that burns the fuel."""

    def setUp(self):
        recipes = {
            "fell": Recipe("fell", {"timber": 1.0}, {}, {"labourer": 1.0}, site_bound=True),
            "burn": Recipe("burn", {"fuel": 1.0}, {"timber": 1.0}, {"labourer": 1.0}),
            "smelt": Recipe("smelt", {"metal": 1.0}, {"fuel": 2.0}, {"labourer": 1.0}),
        }
        self.setup = types.SimpleNamespace(recipes=recipes, site_limits=(SiteLimit("fell", "tile", 100.0),))
        self.record = EconomyRecord.__new__(EconomyRecord)
        self.record.producers = {
            "producer:fell@tile": Producer("producer:fell@tile", "owner", "fell", "tile", 100.0, expected_sales=100.0),
            "producer:burn@tile": Producer("producer:burn@tile", "owner", "burn", "tile", 400.0, expected_sales=400.0),
            "producer:smelt@tile": Producer("producer:smelt@tile", "owner", "smelt", "tile", 200.0, expected_sales=200.0),
        }

    def test_the_fuel_burners_are_held_to_the_timber_and_the_smelters_to_the_fuel(self):
        opening_runs.fit_to_supply(self.setup, self.record)
        made, taken = flows(self.setup, self.record)
        self.assertAlmostEqual(self.record.producers["producer:burn@tile"].expected_sales, 100.0)
        self.assertGreaterEqual(made["fuel"], taken["fuel"] * (1.0 - TOLERANCE))
        self.assertAlmostEqual(self.record.producers["producer:smelt@tile"].expected_sales, 50.0)

    def test_a_good_something_unbound_also_makes_is_not_held(self):
        self.setup.recipes["fuel_import"] = Recipe("fuel_import", {"fuel": 1.0}, {}, {"labourer": 1.0})
        self.assertNotIn("fuel", opening_runs.limited_goods(self.setup.recipes, {"fell": {"tile": object()}}))


if __name__ == "__main__":
    unittest.main()
