"""input_orders_after_hiring: a producer's input orders re-sized to the runs its hired hours make."""

QUICK_TOPIC = True

import unittest

import numpy as np

from sim.economy import input_orders_after_hiring as orders
from sim.economy import rule_sets


class RunsTheHoursMake(unittest.TestCase):
    def test_the_runs_the_hired_hours_staff(self):
        self.assertEqual(orders.runs_the_hours_make(10.0, 20.0, 14.0), 14.0)
        self.assertEqual(orders.runs_the_hours_make(10.0, 20.0, 6.0), 6.0)

    def test_no_more_than_the_most_the_schedule_would_staff(self):
        self.assertEqual(orders.runs_the_hours_make(10.0, 12.0, 14.0), 12.0)

    def test_a_recipe_that_hires_no_hours_keeps_the_runs_the_plan_ordered_for(self):
        self.assertEqual(orders.runs_the_hours_make(10.0, 20.0, None), 10.0)

    def test_no_hours_hired_make_no_runs(self):
        self.assertEqual(orders.runs_the_hours_make(10.0, 20.0, 0.0), 0.0)


class ResizedQuantities(unittest.TestCase):
    def resized(self, quantity, stock, ordered, to_make):
        return orders.resized_quantities(np.array([quantity]), np.array([stock]), np.array([ordered]), np.array([to_make]))[0]

    def test_more_runs_order_what_they_need_less_the_stock_held(self):
        # ten runs needed 700 and 300 in stock: 1000 in all, 100 a run; fourteen runs need 1400, less the 300 held
        self.assertAlmostEqual(self.resized(700.0, 300.0, 10.0, 14.0), 1400.0 - 300.0)

    def test_fewer_runs_order_less(self):
        self.assertAlmostEqual(self.resized(700.0, 300.0, 10.0, 6.0), 600.0 - 300.0)

    def test_runs_the_stock_covers_order_nothing(self):
        self.assertEqual(self.resized(700.0, 300.0, 10.0, 2.0), 0.0)

    def test_the_same_runs_leave_the_order(self):
        self.assertAlmostEqual(self.resized(700.0, 300.0, 10.0, 10.0), 700.0)

    def test_an_order_whose_plan_had_no_runs_is_left_as_it_is(self):
        self.assertEqual(self.resized(700.0, 300.0, 0.0, 5.0), 700.0)

    def test_each_order_is_resized_on_its_own_figures(self):
        found = orders.resized_quantities(np.array([700.0, 50.0]), np.array([300.0, 0.0]), np.array([10.0, 5.0]), np.array([14.0, 10.0]))
        self.assertAlmostEqual(found[0], 1100.0)
        self.assertAlmostEqual(found[1], 100.0)


class BudgetsByValue(unittest.TestCase):
    def test_an_owners_coin_is_split_over_its_orders_by_their_value(self):
        budgets = orders.budgets_by_value(np.array([30.0, 10.0, 5.0]), np.array([0, 0, 1]), np.array([200.0, 50.0]))
        self.assertAlmostEqual(budgets[0], 150.0)
        self.assertAlmostEqual(budgets[1], 50.0)
        self.assertAlmostEqual(budgets[2], 50.0)

    def test_the_budgets_of_an_owner_add_to_its_coin(self):
        budgets = orders.budgets_by_value(np.array([3.0, 4.0, 5.0]), np.array([0, 0, 0]), np.array([90.0]))
        self.assertAlmostEqual(budgets.sum(), 90.0)

    def test_orders_worth_nothing_get_nothing(self):
        budgets = orders.budgets_by_value(np.array([0.0, 0.0]), np.array([0, 0]), np.array([90.0]))
        self.assertEqual(budgets.tolist(), [0.0, 0.0])

    def test_an_owner_with_no_coin_or_a_debit_budgets_nothing(self):
        budgets = orders.budgets_by_value(np.array([3.0, 4.0]), np.array([0, 1]), np.array([0.0, -20.0]))
        self.assertEqual(budgets.tolist(), [0.0, 0.0])


class TheRuleSetsStep(unittest.TestCase):
    def test_search_leaves_the_orders_and_clearing_resizes_them(self):
        self.assertIs(rule_sets.RULE_SETS[rule_sets.SEARCH].input_orders_after_hiring, orders.leave_as_planned)
        self.assertIs(rule_sets.RULE_SETS[rule_sets.CLEARING].input_orders_after_hiring, orders.resize_to_hired_hours)


if __name__ == "__main__":
    unittest.main()
