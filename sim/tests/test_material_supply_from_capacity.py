"""A material's national output is the capacity that exists, never a curve fitted to its price."""
QUICK_TOPIC = True

import types
import unittest

from sim.materials import capacity as material_capacity
from sim.tests import materials_stand_in

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


def module(deposits, made):
    """The materials module over a world with no catalogued commodity, fixed deposits and fixed producer capacities."""
    return materials_stand_in.build(found_deposits=lambda material: deposits.get(material, []),
                                    agent_producer_capacity=lambda material: made.get(material))


class GenericOutput(unittest.TestCase):

    def test_output_is_deposits_plus_producers_and_is_zero_where_neither_exists(self):
        sim = module({"tin_kg": [{"rate_tonnes_per_year": 4.0}]}, {"tin_kg": 1.0, "glass_kg": 8.0})
        self.assertEqual(sim.generic_national_output_uncached("tin_kg"), 5.0)
        self.assertEqual(sim.generic_national_output_uncached("glass_kg"), 8.0)
        self.assertEqual(sim.generic_national_output_uncached("nothing_kg"), 0.0)

    def test_market_share_is_a_declared_open_share_not_a_price_curve(self):
        sim = module({}, {})
        self.assertEqual(sim.generic_market_share_uncached("glass_kg"),
                         material_capacity.DEFAULT_MARKET_SHARE_OF_CAPACITY)


if __name__ == "__main__":
    unittest.main()

