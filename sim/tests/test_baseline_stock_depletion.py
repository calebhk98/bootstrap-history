"""Complaint 473: a good the market clears with no carrying stock is not 'eaten through' by float dust in its first year."""

QUICK_TOPIC = True

import unittest

from sim.economy.baseline_checks import stock_depletion
from sim.economy.year_accounts import GoodAccount, YearAccounts


def year(number, **figures):
    return YearAccounts(number, {"grain": GoodAccount(**figures)})


class StockDepletionTests(unittest.TestCase):
    def test_a_stock_that_was_held_and_is_gone_counts_as_eaten_through(self):
        shares = stock_depletion([year(0, production=1000.0, stock_at_start=500.0, stock_change=0.0),
                                  year(1, production=1000.0, stock_at_start=0.0, stock_change=0.0)])
        self.assertAlmostEqual(shares["grain"], 1.0)

    def test_float_dust_of_a_stock_beside_the_flows_is_not_a_stock(self):
        shares = stock_depletion([year(0, production=1.8e6, final_consumption_bought=1.8e6, stock_at_start=2.0e-10),
                                  year(1, production=1.8e6, final_consumption_bought=1.8e6, stock_at_start=0.0)])
        self.assertNotIn("grain", shares)

    def test_a_small_real_stock_beside_large_flows_still_counts(self):
        shares = stock_depletion([year(0, production=1.8e6, final_consumption_bought=1.8e6, stock_at_start=100.0),
                                  year(1, production=1.8e6, final_consumption_bought=1.8e6, stock_at_start=0.0)])
        self.assertAlmostEqual(shares["grain"], 1.0)


if __name__ == "__main__":
    unittest.main()
