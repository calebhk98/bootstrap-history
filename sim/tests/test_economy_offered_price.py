"""A buyer reads only what is on offer (Complaint 642): a price the market traded at or an ask still posted, never a
remembered price, a bid ceiling or a cost quote."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy.households_basket import Basket, NeedSpec, need_prices
from sim.economy.market_memory import PRICE_REMEMBERED, MarketMemory, YearView
from sim.economy.offered_price import offered_price
from sim.economy.types import (QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING, QUOTE_LOWEST_UNFILLED_ASK,
                               QUOTE_OPENING_ESTIMATE)


def memory_with(price, cleared=False, quote=None, ever_traded=False):
    memory = MarketMemory(prices={"stone|a": price})
    if cleared:
        memory.cleared_prices["stone|a"] = price
    if quote:
        memory.quote_kinds["stone|a"] = quote
    if ever_traded:
        memory.trade_age["stone|a"] = 3
    return memory


class MemoryOfferedPriceTests(unittest.TestCase):
    def test_a_traded_price_is_offered(self):
        self.assertEqual(memory_with(3.0, cleared=True).offered_price("stone|a"), 3.0)

    def test_an_ask_still_posted_is_offered(self):
        self.assertEqual(memory_with(3.0, quote=QUOTE_LOWEST_UNFILLED_ASK).offered_price("stone|a"), 3.0)

    def test_the_opening_estimate_is_offered_until_a_clearing_replaces_it(self):
        self.assertEqual(memory_with(3.0).offered_price("stone|a"), 3.0)

    def test_a_bid_ceiling_is_not_offered(self):
        self.assertIsNone(memory_with(3.0, quote=QUOTE_BEST_UNFILLED_BID).offered_price("stone|a"))

    def test_a_cost_quote_is_not_offered(self):
        self.assertIsNone(memory_with(3.0, quote=QUOTE_COST_COVERING).offered_price("stone|a"))

    def test_a_price_remembered_from_an_old_trade_is_not_offered(self):
        self.assertIsNone(memory_with(3.0, ever_traded=True).offered_price("stone|a"))

    def test_a_market_with_no_price_offers_none(self):
        self.assertIsNone(MarketMemory().offered_price("stone|a"))


class MemoryKindTests(unittest.TestCase):
    def test_a_price_from_an_old_trade_with_no_quote_is_remembered_not_the_opening_estimate(self):
        self.assertEqual(memory_with(3.0, ever_traded=True).price_kind("stone|a"), PRICE_REMEMBERED)

    def test_a_price_no_clearing_replaced_stays_the_opening_estimate(self):
        self.assertEqual(memory_with(3.0).price_kind("stone|a"), QUOTE_OPENING_ESTIMATE)


class ViewOfferedPriceTests(unittest.TestCase):
    def test_the_view_reads_the_memorys_offered_price(self):
        view = YearView(memory_with(3.0, ever_traded=True), None, types.SimpleNamespace(goods=lambda: ()), "coin")
        self.assertIsNone(view.offered_price("stone", "a"))

    def test_a_view_without_the_method_gives_its_price(self):
        self.assertEqual(offered_price(types.SimpleNamespace(price=lambda good, area: 2.0), "stone", "a"), 2.0)


class HouseholdBasketTests(unittest.TestCase):
    def test_a_need_whose_only_good_has_nothing_on_offer_is_unpriced(self):
        basket = Basket((NeedSpec("shelter", 1.0, 1.0, (("stone", 1.0),)),), 0.5, {})
        view = types.SimpleNamespace(area_of=lambda good, tile: "a", price=lambda good, area: 3.0,
                                     offered_price=lambda good, area: None)
        self.assertEqual(need_prices(basket, view, "t"), [])


if __name__ == "__main__":
    unittest.main()
