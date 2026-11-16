"""The cash a household may put into stores: none when its budgets took all the usable cash (what is left is rounding)."""

QUICK_TOPIC = True

import unittest

from sim.economy.opening_demand_kernel import store_pot


class StorePotTests(unittest.TestCase):
    def test_floors_taking_all_the_usable_cash_leave_exactly_no_pot(self):
        usable = 1234.5678
        residue = usable - usable / 1.7000000000000002 * 1.7000000000000002
        self.assertEqual(store_pot(1e6, usable, usable - residue - 1e-13, 10.0 * usable, 1.7 * usable, 1.0 / 1.7, 1.0), 0.0)

    def test_scaled_flexible_budgets_under_a_spending_above_the_cash_leave_exactly_no_pot(self):
        usable = 7.7
        self.assertEqual(store_pot(1e6, usable, usable * (1.0 - 1e-16) - 1e-15, 10.0 * usable, 0.3 * usable, 1.0, 0.4), 0.0)

    def test_budgets_below_the_usable_cash_leave_the_rest_capped_by_the_savings(self):
        self.assertEqual(store_pot(500.0, 100.0, 70.0, 70.0, 40.0, 1.0, 0.9), 30.0)
        self.assertEqual(store_pot(20.0, 100.0, 70.0, 70.0, 40.0, 1.0, 1.0), 20.0)

    def test_no_floors_wanted_and_a_small_spending_leave_the_cash_beyond_it(self):
        self.assertEqual(store_pot(500.0, 100.0, 30.0, 30.0, 0.0, 0.0, 1.0), 70.0)


if __name__ == "__main__":
    unittest.main()
