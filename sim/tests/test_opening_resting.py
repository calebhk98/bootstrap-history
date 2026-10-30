"""The opening is a resting state of the current rules (Eurace user manual chapter 10: stocks that agree with the
rules from the start). Each rule below is one plain function over written-out inputs."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import households_buffer_stock, inventory, opening_resting
from sim.economy.producers import OUTPUT_CHANGE_SHARE_PER_YEAR


class RestingPurseTests(unittest.TestCase):
    def test_a_household_with_no_shares_opens_with_no_cash_beyond_the_income_it_is_about_to_receive(self):
        self.assertEqual(opening_resting.resting_household_purse(mean_income=12.0, share_wealth=0.0), 0.0)

    def test_spending_at_that_purse_is_the_income(self):
        income = 12.0
        purse = opening_resting.resting_household_purse(income, share_wealth=0.0)
        self.assertAlmostEqual(households_buffer_stock.spending_budget(income, purse + income, 0.0), income)

    def test_a_household_with_shares_holds_cash_up_to_the_wealth_target_and_spends_its_income(self):
        income, shares = 12.0, 1.0
        purse = opening_resting.resting_household_purse(income, share_wealth=shares)
        target = households_buffer_stock.WEALTH_INCOME_RATIO_TARGET / 12.0 * income
        self.assertAlmostEqual(purse + income + shares, target)
        self.assertAlmostEqual(households_buffer_stock.spending_budget(income, purse + income, shares), income)

    def test_shares_beyond_the_target_leave_no_cash_to_hold(self):
        self.assertEqual(opening_resting.resting_household_purse(12.0, share_wealth=100.0), 0.0)


class RestingStockTests(unittest.TestCase):
    def test_a_producer_opens_holding_the_target_stock_of_each_output_for_its_expected_sales(self):
        stock = opening_resting.resting_output_stock(120.0, {"grain": 2.0, "straw": 1.0})
        self.assertEqual(stock, {"grain": inventory.target_stock(120.0) * 2.0, "straw": inventory.target_stock(120.0)})

    def test_no_expected_sales_hold_no_stock(self):
        self.assertEqual(opening_resting.resting_output_stock(0.0, {"grain": 2.0}), {})


class SpareCapacityTests(unittest.TestCase):
    def test_plant_that_wears_a_twentieth_a_year_is_sized_to_cover_sales_and_the_growth_band_after_wear(self):
        recipe = types.SimpleNamespace(plant_life_years=20.0)
        capacity = 1.0 + opening_resting.spare_capacity_share(recipe)
        self.assertAlmostEqual(capacity * (1.0 - 1.0 / 20.0) - OUTPUT_CHANGE_SHARE_PER_YEAR * capacity, 1.0)

    def test_a_recipe_with_no_plant_keeps_the_stated_spare_share(self):
        recipe = types.SimpleNamespace(plant_life_years=0.0)
        self.assertEqual(opening_resting.spare_capacity_share(recipe), opening_resting.OPENING_SPARE_CAPACITY_SHARE)

    def test_plant_that_wears_out_faster_than_the_band_allows_keeps_the_stated_share(self):
        recipe = types.SimpleNamespace(plant_life_years=1.2)
        self.assertEqual(opening_resting.spare_capacity_share(recipe), opening_resting.OPENING_SPARE_CAPACITY_SHARE)


if __name__ == "__main__":
    unittest.main()
