"""A market with buyers and no sellers reports a cost-covering quote, so a stale low price stops drawing
households' food budget to a food nobody sells."""

QUICK_TOPIC = True

import unittest

from sim.economy import market_quote
from sim.economy.types import QUOTE_COST_COVERING, Bid

PORRIDGE = "porridge_kg"


class QuoteWithNoOffersTests(unittest.TestCase):
    def test_buyers_and_no_sellers_with_a_maker_able_to_produce_quote_the_cost(self):
        quote = market_quote.no_trade_quote([Bid("buyer", PORRIDGE, "area", "tile", 1.0, 0.0, 1.0, 0.0, 10.0)], [], cost=3.0)
        self.assertEqual((quote.kind, quote.price), (QUOTE_COST_COVERING, 3.0))

    def test_without_a_cost_or_a_finite_bid_there_is_nothing_to_quote(self):
        self.assertIsNone(market_quote.no_trade_quote([Bid("buyer", PORRIDGE, "area", "tile", 1.0, 0.0, 1.0, 0.0, 10.0)], []))



if __name__ == "__main__":
    unittest.main()
