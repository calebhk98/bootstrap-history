"""A producer's costs laid out this year are repaid by selling its output, so they are not a shortfall that
presses it to undercut the market (Complaint 472)."""

QUICK_TOPIC = True

import unittest

from sim.economy import seller_cash


class SellerCashTests(unittest.TestCase):
    def test_cash_laid_out_this_year_is_not_counted_as_a_shortfall_in_full(self):
        target, laid_out = 100.0, 80.0
        cash_after_costs = target - laid_out
        shortfall = seller_cash.shortfall_to_raise(target, cash_after_costs, laid_out)
        self.assertLess(shortfall, laid_out)
        self.assertAlmostEqual(shortfall, (1.0 - seller_cash.LAID_OUT_COST_REPAID_SHARE) * laid_out)

    def test_a_producer_short_of_its_target_before_the_year_still_has_a_shortfall(self):
        shortfall = seller_cash.shortfall_to_raise(100.0, 0.0, 10.0)
        self.assertGreater(shortfall, 90.0 - 1e-9)

    def test_a_producer_at_its_target_has_none(self):
        self.assertEqual(seller_cash.shortfall_to_raise(100.0, 150.0, 30.0), 0.0)


if __name__ == "__main__":
    unittest.main()
