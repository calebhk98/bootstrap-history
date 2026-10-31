"""The mint's staffing size and funding (sim/economy/mint_staffing.py, mint_labour.py)."""

QUICK_TOPIC = True

import unittest

from sim.economy import mint_staffing
from sim.economy.mint_labour import scale_bids_to_funds
from sim.economy.types import LabourBid


class StaffedMoney(unittest.TestCase):
    def test_a_wish_far_beyond_wear_is_staffed_to_a_multiple_of_wear(self):
        worn = 10.0
        staffed = mint_staffing.staffed_money(monetisation=1.0e6, worn_money=worn)
        self.assertAlmostEqual(staffed, mint_staffing.MINT_STAFFING_MULTIPLE_OF_WEAR * worn)

    def test_a_small_wish_is_staffed_as_wished(self):
        self.assertAlmostEqual(mint_staffing.staffed_money(monetisation=11.0, worn_money=10.0), 11.0)


class HourValue(unittest.TestCase):
    def test_the_value_of_an_hour_is_a_share_of_the_coin_value_over_the_hours_to_strike_it(self):
        value = mint_staffing.hour_value(parity=1000.0, hours_per_fine_kilogram=4.0)
        self.assertAlmostEqual(value, mint_staffing.MINT_LABOUR_SHARE_OF_COIN_VALUE * 250.0)

    def test_a_recipe_with_no_hours_is_worth_nothing_per_hour(self):
        self.assertEqual(mint_staffing.hour_value(parity=1000.0, hours_per_fine_kilogram=0.0), 0.0)


class GoodsBudgetCut(unittest.TestCase):
    def test_unplanned_cash_pays_first_and_the_goods_line_gives_up_the_rest(self):
        cut = mint_staffing.goods_budget_cut(balance=100.0, wage_budget=30.0, goods_budget=60.0, funded=25.0)
        self.assertAlmostEqual(cut, 15.0)

    def test_nothing_is_cut_where_unplanned_cash_covers_it(self):
        self.assertEqual(mint_staffing.goods_budget_cut(balance=100.0, wage_budget=30.0, goods_budget=20.0, funded=40.0), 0.0)

    def test_the_cut_is_never_more_than_the_goods_line(self):
        self.assertAlmostEqual(mint_staffing.goods_budget_cut(balance=90.0, wage_budget=30.0, goods_budget=60.0, funded=500.0), 60.0)


class ScaleToFunds(unittest.TestCase):
    def test_hours_shrink_together_until_the_bill_at_the_ceilings_is_the_funds(self):
        bids = [LabourBid("mint", "a", "area", 100.0, 2.0), LabourBid("mint", "b", "area", 50.0, 4.0)]
        scaled = scale_bids_to_funds(bids, funded=200.0)          # the bill is 400
        self.assertAlmostEqual(sum(bid.hours * bid.maximum_wage for bid in scaled), 200.0)
        self.assertAlmostEqual(scaled[0].hours / scaled[1].hours, 2.0)

    def test_a_funded_bill_is_left_as_it_is(self):
        bids = [LabourBid("mint", "a", "area", 100.0, 2.0)]
        self.assertEqual(scale_bids_to_funds(bids, funded=500.0), bids)

    def test_no_funds_means_no_bids(self):
        self.assertEqual(scale_bids_to_funds([LabourBid("mint", "a", "area", 100.0, 2.0)], funded=0.0), [])


if __name__ == "__main__":
    unittest.main()
