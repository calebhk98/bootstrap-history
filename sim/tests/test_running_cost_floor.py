"""Complaint 135: a producer that has sunk its capital offers at its running cost, read from the recipe's own split
of its cost into running and capital parts. Build decisions keep paying back the capital (the full cost)."""

QUICK_TOPIC = True

import unittest

from sim.prices import entry_cost, solve_prices
from sim.tests.test_capital_charge import WAGES, works_entry

RATE = 0.12


def book(production):
    return entry_cost.CostBook({"ore_kg": 1.0}.get, WAGES.get, RATE, production=production)


class RunningCostSplitTests(unittest.TestCase):
    def test_the_solver_can_cost_an_entry_without_its_plant(self):
        full = solve_prices.recipe_cost_and_allocation(
            "widget_kg", works_entry(), {"ore_kg": 1.0}, WAGES, interest_rate=RATE)[1]["widget_kg"]
        running = solve_prices.recipe_cost_and_allocation(
            "widget_kg", works_entry(), {"ore_kg": 1.0}, WAGES, interest_rate=RATE,
            include_capital=False)[1]["widget_kg"]
        self.assertAlmostEqual(running, (10.0 * 1.0 + 5.0 * 1.0) / 10.0)
        self.assertGreater(full, running)

    def test_an_entry_with_no_plant_costs_the_same_either_way(self):
        entry = dict(works_entry(), capital=[])
        both = [solve_prices.recipe_cost_and_allocation(
            "widget_kg", entry, {"ore_kg": 1.0}, WAGES, include_capital=flag)[1]["widget_kg"]
            for flag in (True, False)]
        self.assertEqual(both[0], both[1])


class CostBookTests(unittest.TestCase):
    def test_running_cost_is_below_full_cost_by_the_plants_repayment(self):
        cost_book = book({"widget_kg": works_entry()})
        full = cost_book.unit_cost("widget_kg", "widget_kg")
        running = cost_book.running_unit_cost("widget_kg", "widget_kg")
        self.assertIsNotNone(running)
        self.assertLess(running, full)


if __name__ == "__main__":
    unittest.main()
