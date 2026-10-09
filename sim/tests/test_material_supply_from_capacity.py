"""A material's national output is the capacity that exists, never a curve fitted to its price."""
QUICK_TOPIC = True

import inspect
import types
import unittest

from sim.engine import economy_materials, material_capacity
from sim.engine.economy_materials import MaterialSupplyMixin

PRODUCER = types.SimpleNamespace
RECIPE = types.SimpleNamespace


class Capacity(unittest.TestCase):

    def test_mined_capacity_is_the_sum_of_deposit_working_rates(self):
        rows = [{"rate_tonnes_per_year": 30.0}, {"rate_tonnes_per_year": 12.5}, {}]
        self.assertEqual(material_capacity.mined_capacity_tonnes(rows), 42.5)
        self.assertEqual(material_capacity.mined_capacity_tonnes([]), 0.0)

    def test_producer_capacity_is_runs_times_output_per_run_in_tonnes(self):
        producers = [PRODUCER(recipe_id="a", capacity_runs=10.0), PRODUCER(recipe_id="b", capacity_runs=5.0),
                     PRODUCER(recipe_id="gone", capacity_runs=99.0)]
        recipes = {"a": RECIPE(outputs={"glass_kg": 200.0}), "b": RECIPE(outputs={"glass_kg": 100.0, "ash_kg": 7.0})}
        self.assertAlmostEqual(material_capacity.producer_capacity_tonnes(producers, recipes, "glass_kg", 0.001), 2.5)
        self.assertEqual(material_capacity.producer_capacity_tonnes(producers, recipes, "tin_kg", 0.001), 0.0)


class FakeSim(MaterialSupplyMixin):
    """Just enough of a Sim for the generic output: a ledger with no commodity and fixed capacities."""

    def __init__(self, deposits, made):
        self._deposits, self._made = deposits, made

    def _commodity_ledger(self):
        return types.SimpleNamespace(commodities={})

    def found_deposits(self, material):
        return self._deposits.get(material, [])

    def producer_capacity_tonnes(self, material):
        return self._made.get(material, 0.0)


class GenericOutput(unittest.TestCase):

    def test_output_is_deposits_plus_producers_and_is_zero_where_neither_exists(self):
        sim = FakeSim({"tin_kg": [{"rate_tonnes_per_year": 4.0}]}, {"tin_kg": 1.0, "glass_kg": 8.0})
        self.assertEqual(sim._generic_national_output_uncached("tin_kg"), 5.0)
        self.assertEqual(sim._generic_national_output_uncached("glass_kg"), 8.0)
        self.assertEqual(sim._generic_national_output_uncached("nothing_kg"), 0.0)

    def test_market_share_is_a_declared_open_share_not_a_price_curve(self):
        sim = FakeSim({}, {})
        self.assertEqual(sim._generic_market_share_uncached("glass_kg"),
                         material_capacity.DEFAULT_MARKET_SHARE_OF_CAPACITY)

    def test_no_price_fit_remains(self):
        source = inspect.getsource(economy_materials)
        for name in ("GENERIC_OUTPUT_ANCHOR", "GENERIC_OUTPUT_PRICE_EXPONENT", "GENERIC_MARKET_SHARE_SCALE",
                     "GENERIC_MARKET_SHARE_PRICE_EXPONENT", "_hours_price_per_kg"):
            self.assertNotIn(name, source)


if __name__ == "__main__":
    unittest.main()

