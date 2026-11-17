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


class FitToSupplyLoopTests(unittest.TestCase):
    """A kiln whose plant is the metal smelted with its own fuel: timber short of what the kilns were sized for must hold
    the kilns to the timber and the smelters to the fuel, not send both round the loop to nothing."""

    def setUp(self):
        recipes = {
            "fell": Recipe("fell", {"timber": 1.0}, {}, {"labourer": 1.0}, site_bound=True),
            "burn": Recipe("burn", {"fuel": 1.0}, {"timber": 1.0}, {"labourer": 1.0}, {"metal": 1.0}, {}, 10.0),
            "smelt": Recipe("smelt", {"metal": 1.0}, {"fuel": 2.0}, {"labourer": 1.0}),
            "forge": Recipe("forge", {"tools": 1.0}, {"metal": 1.0}, {"smith": 1.0}),
        }
        self.setup = types.SimpleNamespace(recipes=recipes, site_limits=(SiteLimit("fell", "tile", 100.0),))
        self.record = EconomyRecord.__new__(EconomyRecord)
        self.record.producers = {
            "producer:fell@tile": Producer("producer:fell@tile", "owner", "fell", "tile", 100.0, expected_sales=100.0),
            "producer:burn@tile": Producer("producer:burn@tile", "owner", "burn", "tile", 200.0, expected_sales=200.0),
            "producer:smelt@tile": Producer("producer:smelt@tile", "owner", "smelt", "tile", 100.0, expected_sales=100.0),
            "producer:forge@tile": Producer("producer:forge@tile", "owner", "forge", "tile", 80.0, expected_sales=80.0),
        }

    def test_a_makers_plant_upkeep_is_served_before_the_other_users_are_cut(self):
        opening_runs.fit_to_supply(self.setup, self.record)
        sales = {key.split(":")[1].split("@")[0]: producer.expected_sales for key, producer in self.record.producers.items()}
        self.assertAlmostEqual(sales["burn"], 100.0)       # the timber there is
        self.assertAlmostEqual(sales["smelt"], 50.0)       # the fuel the kilns then make
        self.assertAlmostEqual(sales["forge"], 40.0)       # the metal left once the kilns' upkeep (a tenth of a unit a run) is taken


if __name__ == "__main__":
    unittest.main()
