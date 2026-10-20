"""A market with offers and no bids quotes its lowest unfilled ask instead of keeping a price, and the first trade
after such quiet years moves the remembered price only part of the way."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import market_memory_asks as asks
from sim.economy import market_quote
from sim.economy.market_memory import MarketMemory
from sim.economy.types import QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK, Bid, Offer


def offer(ask):
    return Offer("seller", "limestone_kg", "area", "tile", 1.0, ask)


def bid(budget=10.0):
    return Bid("buyer", "limestone_kg", "area", "tile", 1.0, 0.0, 1.0, 0.0, budget)


class NoBidQuoteTests(unittest.TestCase):
    def test_a_market_with_offers_and_no_bids_quotes_the_lowest_unfilled_ask(self):
        quote = market_quote.no_trade_quote([], [offer(500.0), offer(100.0)])
        self.assertEqual((quote.kind, quote.price), (QUOTE_LOWEST_UNFILLED_ASK, 100.0))

    def test_a_market_with_a_live_bid_below_every_ask_quotes_the_bid(self):
        capped = dataclasses.replace(bid(), maximum_price=50.0)
        quote = market_quote.no_trade_quote([capped], [offer(100.0)])
        self.assertEqual(quote.price, 50.0)
        self.assertEqual(quote.kind, QUOTE_BEST_UNFILLED_BID)

    def test_a_broke_buyer_is_no_bid(self):
        quote = market_quote.no_trade_quote([bid(budget=0.0)], [offer(100.0)])
        self.assertEqual((quote.kind, quote.price), (QUOTE_LOWEST_UNFILLED_ASK, 100.0))

    def test_nothing_offered_and_nothing_bid_quotes_nothing(self):
        self.assertIsNone(market_quote.no_trade_quote([], []))


class ResumedTradeTests(unittest.TestCase):
    def test_years_without_bids_are_counted_and_reset(self):
        memory = MarketMemory()
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 0)
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 1)
        self.assertEqual(asks.note_bids(memory, "k", [bid()], [offer(1.0)]), 2)
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 0)

    def test_first_trade_after_quiet_years_moves_part_of_the_way(self):
        price = asks.price_after_resumed_trade(10.0, 1000.0, 3)
        self.assertGreater(price, 10.0)
        self.assertLess(price, 1000.0)

    def test_a_market_that_was_bid_in_adopts_the_volume_rule_price(self):
        self.assertEqual(asks.price_after_resumed_trade(10.0, 1000.0, 0), 1000.0)

    def test_the_count_is_saved_with_the_memory(self):
        self.assertIn("years_without_bids", MarketMemory().__dict__)


if __name__ == "__main__":
    unittest.main()
