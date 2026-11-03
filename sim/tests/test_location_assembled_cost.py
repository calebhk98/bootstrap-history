"""A run's cost on a tile read in parts (variable cost once, carriage per demand) equals `cost_per_run`."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import location, unit_cost
from sim.economy.types import Recipe


class AssembledCostTests(unittest.TestCase):
    def test_parts_give_the_cost_per_run_of_the_whole(self):
        recipe = Recipe("smelt", {"ore": 3.0}, {"metal": 1.0}, {"smith": 2.0})
        prices, wages = {"ore": 4.0}, {"smith": 7.0}
        variable = unit_cost.variable_cost_per_run(recipe, prices, wages, 0.5)
        for carriage, factor, tonnes, haul in ((0.3, 0.8, 0.002, 1.5), (0.0, 1.0, 0.0, 0.0), (9.0, 1.3, 0.1, 0.25)):
            self.assertEqual(location.assembled_cost(variable, carriage, factor, tonnes, haul),
                             location.cost_per_run(recipe, wages, prices, 0.5, carriage, factor, tonnes, haul))
        self.assertEqual(location.cost_per_run(recipe, wages, prices, 0.5, 1.0, 0.0), math.inf)


class SiteCostTests(unittest.TestCase):
    def test_a_trade_with_no_wage_costs_infinity_not_a_crash(self):
        self.assertEqual(location.site_cost(None, 0.3, 0.8, 0.002, 1.5), math.inf)

    def test_a_priced_run_costs_its_assembled_cost(self):
        self.assertEqual(location.site_cost(5.0, 0.3, 0.8, 0.002, 1.5), location.assembled_cost(5.0, 0.3, 0.8, 0.002, 1.5))

    def test_no_yield_costs_infinity(self):
        self.assertEqual(location.site_cost(5.0, 0.3, 0.0, 0.002, 1.5), math.inf)


if __name__ == "__main__":
    unittest.main()
