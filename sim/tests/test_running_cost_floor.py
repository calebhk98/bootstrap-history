"""Complaint 135: a producer that has sunk its capital offers at its running cost, read from the recipe's own split
of its cost into running and capital parts. Build decisions keep paying back the capital (the full cost)."""

QUICK_TOPIC = True

import unittest

from sim.prices import solve_prices_core
from sim.tests.test_capital_charge import WAGES, works_entry

RATE = 0.12


class RunningCostSplitTests(unittest.TestCase):
    def test_the_solver_can_cost_an_entry_without_its_plant(self):
        full = solve_prices_core.recipe_cost_and_allocation(
            "widget_kg", works_entry(), {"ore_kg": 1.0}, WAGES, interest_rate=RATE)[1]["widget_kg"]
        running = solve_prices_core.recipe_cost_and_allocation(
            "widget_kg", works_entry(), {"ore_kg": 1.0}, WAGES, interest_rate=RATE,
            include_capital=False)[1]["widget_kg"]
        self.assertAlmostEqual(running, (10.0 * 1.0 + 5.0 * 1.0) / 10.0)
        self.assertGreater(full, running)

    def test_an_entry_with_no_plant_costs_the_same_either_way(self):
        entry = dict(works_entry(), capital=[])
        both = [solve_prices_core.recipe_cost_and_allocation(
            "widget_kg", entry, {"ore_kg": 1.0}, WAGES, include_capital=flag)[1]["widget_kg"]
            for flag in (True, False)]
        self.assertEqual(both[0], both[1])


if __name__ == "__main__":
    unittest.main()
