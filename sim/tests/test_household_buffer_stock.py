"""Eurace's consumption budget: mean net income, a share of cash, and a share of share wealth over its target."""

QUICK_TOPIC = True

import unittest

from sim.economy import households_buffer_stock as stock


class ShareWealthCarriedTests(unittest.TestCase):
    def test_the_wealth_recorded_at_the_last_close_is_the_wealth_the_year_starts_with(self):
        self.assertEqual(stock.share_wealth_carried(recorded=500.0, current=40.0), 500.0)

    def test_a_household_with_no_record_reads_the_current_wealth(self):
        self.assertEqual(stock.share_wealth_carried(recorded=None, current=40.0), 40.0)

    def test_a_recorded_zero_is_a_record(self):
        self.assertEqual(stock.share_wealth_carried(recorded=0.0, current=40.0), 0.0)


class SpendingBudgetTests(unittest.TestCase):
    def test_the_yearly_share_compounds_the_monthly_share(self):
        self.assertAlmostEqual(stock.yearly_cash_share(0.01), 1.0 - 0.99 ** 12)

    def test_without_shares_the_budget_is_income_plus_the_yearly_share_of_cash(self):
        self.assertAlmostEqual(stock.spending_budget(1000.0, 5000.0, 0.0), 1000.0 + stock.yearly_cash_share() * 5000.0)

    def test_money_lent_is_in_the_account_the_share_applies_to(self):
        self.assertAlmostEqual(stock.spending_budget(1000.0, 5000.0, 0.0, claims=5000.0),
                               1000.0 + stock.yearly_cash_share() * 10000.0)

    def test_the_budget_never_exceeds_cash(self):
        self.assertEqual(stock.spending_budget(1000.0, 400.0, 0.0), 400.0)

    def test_shares_at_the_target_add_nothing(self):
        at_target = stock.WEALTH_INCOME_RATIO_TARGET / stock.MONTHS_PER_YEAR * 1000.0
        self.assertAlmostEqual(stock.spending_budget(1000.0, 9000.0, at_target), 1000.0 + stock.yearly_cash_share() * 9000.0)

    def test_shares_over_the_target_raise_the_budget_and_under_it_cut_it(self):
        at_target = stock.WEALTH_INCOME_RATIO_TARGET / stock.MONTHS_PER_YEAR * 1000.0
        self.assertGreater(stock.spending_budget(1000.0, 9000.0, 2.0 * at_target), stock.spending_budget(1000.0, 9000.0, at_target))
        self.assertLess(stock.spending_budget(1000.0, 9000.0, 0.5 * at_target), stock.spending_budget(1000.0, 9000.0, at_target))

    def test_no_income_and_no_cash_spends_nothing(self):
        self.assertEqual(stock.spending_budget(0.0, 0.0, 0.0), 0.0)


class MeanNetIncomeTests(unittest.TestCase):
    def test_the_mean_is_of_this_year_and_last(self):
        self.assertEqual(stock.mean_net_income(100.0, 300.0), 200.0)

    def test_with_no_last_year_it_is_this_years(self):
        self.assertEqual(stock.mean_net_income(100.0, 0.0), 100.0)


if __name__ == "__main__":
    unittest.main()
