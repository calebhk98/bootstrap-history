"""The cash a household has left for flexible spending after its floors: none when the floors take all the usable cash."""

QUICK_TOPIC = True

import unittest

from sim.economy.opening_demand_kernel import flexible_budget_left


class FlexibleBudgetLeftTests(unittest.TestCase):
    def test_floors_taking_all_the_usable_cash_leave_exactly_nothing(self):
        usable, floor_wanted = 100.0, 137.3
        floor_scale = usable / floor_wanted
        self.assertEqual(flexible_budget_left(usable, 500.0, floor_wanted, floor_scale), 0.0)

    def test_rounding_noise_in_the_scaled_floors_is_not_a_budget(self):
        # usable / floor_wanted * floor_wanted is not usable to the last bit for most values
        for usable in (0.1, 7.7, 1234.5678, 1e-3, 3.3e5):
            floor_wanted = usable * 1.7000000000000002
            floor_scale = usable / floor_wanted
            self.assertEqual(flexible_budget_left(usable, 10.0 * usable, floor_wanted, floor_scale), 0.0, usable)

    def test_affordable_floors_leave_the_spending_beyond_them_capped_by_the_cash(self):
        self.assertEqual(flexible_budget_left(100.0, 70.0, 40.0, 1.0), 30.0)
        self.assertEqual(flexible_budget_left(100.0, 300.0, 40.0, 1.0), 60.0)
        self.assertEqual(flexible_budget_left(100.0, 10.0, 40.0, 1.0), 0.0)

    def test_no_floors_wanted_leaves_the_spending_capped_by_the_cash(self):
        # floor_scale is zero where no floor is wanted: that is not floors taking the cash
        self.assertEqual(flexible_budget_left(100.0, 70.0, 0.0, 0.0), 70.0)
        self.assertEqual(flexible_budget_left(100.0, 300.0, 0.0, 0.0), 100.0)


if __name__ == "__main__":
    unittest.main()
