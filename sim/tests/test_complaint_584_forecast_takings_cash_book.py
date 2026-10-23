"""Complaints/584: a concern's forecast says what it stands on. Goods nobody has sold have no market price, so the
forecast is the long-run figure and says so; once sold, the market's price applies. The rule is
`concern_earnings.forecast_basis`; that the forecast, the year's takings and the cash book read one function is not
tested through a game."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import business_books
from sim.engine import concern_earnings as earnings

takings_of_size = business_books.takings_of_size


class ForecastBasisTests(unittest.TestCase):
    def test_goods_with_no_market_are_quoted_at_long_run_takings(self):
        self.assertEqual(earnings.forecast_basis(False), "long_run_no_market_yet")

    def test_goods_the_market_prices_are_quoted_at_the_market(self):
        self.assertEqual(earnings.forecast_basis(True), "market")


class NoMarketYetTests(unittest.TestCase):
    def test_a_concern_whose_goods_have_no_market_is_quoted_at_long_run_takings_not_nothing(self):
        factor = earnings.output_market_factor(False, lambda: self.fail("no market to read"))
        takings = earnings.takings_at(500.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        self.assertEqual(factor, 1.0)
        self.assertEqual(takings_of_size(takings, 1.0, factor), takings)
        self.assertGreater(takings, 0.0)

    def test_once_the_goods_sell_the_markets_factor_applies(self):
        self.assertEqual(earnings.output_market_factor(True, lambda: 0.8), 0.8)


if __name__ == "__main__":
    unittest.main()
