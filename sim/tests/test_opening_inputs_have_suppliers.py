"""Complaint 570: at the opening every input the sized producers take is made, in the quantity they take, by the
producers sized beside them. A fuel made from timber is held to the timber, and so is every processor that burns it."""
import types
import unittest

from sim.economy import inventory, opening, opening_runs
from sim.economy.producers import Producer
from sim.economy.record import EconomyRecord
from sim.economy.types import Recipe, SiteLimit
from sim.engine.economy_port_setup import build_setup
from sim.tests import harness

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


class OpeningInputsHaveSuppliersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = build_setup(harness.unopened_sim(civ="rome_100ad"))
        cls.record, cls.area_map, _carriage = opening.open_economy(cls.setup)

    def test_every_input_is_made_in_the_quantity_the_producers_take(self):
        made, taken = flows(self.setup, self.record)
        short = {good: (made.get(good, 0.0), wanted) for good, wanted in taken.items()
                 if made.get(good, 0.0) < wanted * (1.0 - TOLERANCE)}
        self.assertEqual(short, {})

    def test_charcoal_is_made_where_the_smelters_take_it(self):
        made, taken = flows(self.setup, self.record)
        self.assertGreater(taken["charcoal_kg"], 0.0)
        self.assertGreaterEqual(made["charcoal_kg"], taken["charcoal_kg"] * (1.0 - TOLERANCE))


class OpeningInputStockTests(unittest.TestCase):
    """A producer opens holding the working stock of its inputs, not a year's: a year's would leave the suppliers
    no sales in the first year, and the buyers would then find the input scarce."""

    @classmethod
    def setUpClass(cls):
        cls.setup = build_setup(harness.unopened_sim(civ="rome_100ad"))
        cls.record, _area_map, _carriage = opening.open_economy(cls.setup)

    def test_no_producer_holds_more_of_an_input_than_its_working_stock(self):
        too_much = {}
        for producer_id, producer in self.record.producers.items():
            recipe = self.setup.recipes[producer.recipe_id]
            runs = inventory.target_stock(producer.expected_sales * (1.0 + opening.OPENING_SPARE_CAPACITY_SHARE))
            for good, per_run in recipe.inputs.items():
                held = self.record.book.stock(producer_id, good, producer.tile)
                if held > runs * per_run * (1.0 + TOLERANCE) + TOLERANCE:
                    too_much[(producer_id, good)] = held
        self.assertEqual(too_much, {})

    def test_the_stocks_are_held_at_all(self):
        held = sum(self.record.book.stock(producer_id, "iron_ore_kg", producer.tile)
                   for producer_id, producer in self.record.producers.items())
        self.assertGreater(held, 0.0)


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
