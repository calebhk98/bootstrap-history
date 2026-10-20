"""Complaint 642: a market has a price only for a year in which it traded. A market that did not trade reports
a quote, named as what it is (the best unfilled bid, the lowest unfilled ask, or a cost-covering quote), and
the price index follows the markets that traded."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import goods_market, market_quote
from sim.economy.market_memory import MarketMemory, YearView
from sim.economy.national_prices import national_prices
from sim.economy.types import (QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING, QUOTE_LOWEST_UNFILLED_ASK, Bid, Offer)

GOOD, AREA, TILE = "grain", "area", "tile"
LAST_PRICE = 7.0


def bid(quantity=10.0, maximum_price=float("inf"), budget=1e9):
    return Bid("buyer", GOOD, AREA, TILE, quantity, 0.0, 1.0, 0.0, budget, 0, maximum_price)


def offer(ask, quantity=10.0):
    return Offer("seller", GOOD, AREA, TILE, quantity, ask)


def clear(bids, offers):
    return goods_market.clear(bids, offers, GOOD, AREA, "coin", LAST_PRICE)


class ClearingTests(unittest.TestCase):
    def test_a_trade_gives_its_price_and_no_quote(self):
        result = clear([bid()], [offer(2.0)])
        self.assertGreater(result.quantity, 0.0)
        self.assertEqual(result.traded_price, result.price)
        self.assertGreaterEqual(result.traded_price, 2.0)
        self.assertIsNone(result.quote)

    def test_asks_above_every_bid_give_no_price_and_the_best_unfilled_bid(self):
        result = clear([bid(maximum_price=3.0), bid(maximum_price=4.0)], [offer(6.0)])
        self.assertEqual(result.quantity, 0.0)
        self.assertIsNone(result.traded_price)
        self.assertEqual((result.quote.kind, result.quote.price), (QUOTE_BEST_UNFILLED_BID, 4.0))

    def test_offers_and_no_bids_give_no_price_and_the_lowest_unfilled_ask(self):
        result = clear([], [offer(5.0), offer(3.0)])
        self.assertIsNone(result.traded_price)
        self.assertEqual((result.quote.kind, result.quote.price), (QUOTE_LOWEST_UNFILLED_ASK, 3.0))

    def test_bids_and_no_offers_give_no_price_and_the_last_price_is_not_shown_as_one(self):
        result = clear([bid(maximum_price=4.0)], [])
        self.assertIsNone(result.traded_price)
        self.assertEqual((result.quote.kind, result.quote.price), (QUOTE_BEST_UNFILLED_BID, 4.0))

    def test_a_maker_able_to_produce_gives_a_cost_covering_quote_for_buyers_nobody_serves(self):
        quote = market_quote.no_trade_quote([bid()], [], cost=2.5)
        self.assertEqual((quote.kind, quote.price), (QUOTE_COST_COVERING, 2.5))

    def test_a_market_with_nothing_posted_quotes_nothing(self):
        result = clear([], [])
        self.assertIsNone(result.traded_price)
        self.assertIsNone(result.quote)


class ReaderTests(unittest.TestCase):
    def record(self, prices, quotes, weights):
        memory = MarketMemory(prices=prices, quote_kinds=quotes, volume_weights=weights)
        return types.SimpleNamespace(memory=memory, volumes={})

    def test_the_price_index_follows_the_areas_that_traded(self):
        record = self.record({"grain|a": 2.0, "grain|b": 90.0}, {"grain|b": QUOTE_LOWEST_UNFILLED_ASK},
                             {"grain|a": 10.0, "grain|b": 10.0})
        self.assertEqual(national_prices(record)["grain"], 2.0)

    def test_a_good_no_area_traded_shows_its_quote_figure(self):
        record = self.record({"grain|b": 90.0}, {"grain|b": QUOTE_LOWEST_UNFILLED_ASK}, {"grain|b": 0.0})
        self.assertEqual(national_prices(record)["grain"], 90.0)

    def test_a_view_says_when_its_price_is_a_quote(self):
        memory = MarketMemory(prices={"grain|a": 3.0}, quote_kinds={"grain|a": QUOTE_BEST_UNFILLED_BID},
                              cleared_prices={})
        view = YearView(memory, None, types.SimpleNamespace(goods=lambda: ["grain"]), "coin")
        self.assertEqual(view.quote_kind("grain", "a"), QUOTE_BEST_UNFILLED_BID)
        self.assertIsNone(view.cleared_price("grain", "a"))


if __name__ == "__main__":
    unittest.main()
