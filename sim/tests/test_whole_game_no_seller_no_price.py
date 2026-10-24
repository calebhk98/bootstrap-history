"""Complaints 38 and 642: a price needs a seller and a trade. A market where buyers bid and nobody offers shows no traded
price, only a quote named as what it is (a cost-covering quote when a maker could make the good, else the best unfilled
bid); an import is bounded by what the partner makes and the carriers lift. Complaint 640: the rules are called on
books and numbers built here; the unit-price wiring is in test_offers_unit_price_and_foreman_reply."""
QUICK_TOPIC = True

import unittest

from sim.economy import goods_market, market_quote
from sim.economy.types import QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING, Bid
from sim.engine.goods_market_imports import import_tonnes_left

GOOD, AREA, TILE = "cobalt_kg", "area", "tile"
LAST_PRICE = 7.0


def bid(maximum_price=float("inf"), budget=1e9):
    return Bid("buyer", GOOD, AREA, TILE, 10.0, 0.0, 1.0, 0.0, budget, 0, maximum_price)


class NoSellerNoPriceTests(unittest.TestCase):

    def test_buyers_and_no_seller_give_no_traded_price_and_not_the_last_one_remembered(self):
        result = goods_market.clear([bid(maximum_price=4.0)], [], GOOD, AREA, "coin", LAST_PRICE)
        self.assertIsNone(result.traded_price)
        self.assertEqual(result.quantity, 0.0)
        self.assertEqual((result.quote.kind, result.quote.price), (QUOTE_BEST_UNFILLED_BID, 4.0))

    def test_where_a_maker_could_make_it_the_quote_is_what_covers_the_cost_and_is_named_so(self):
        quote = market_quote.no_trade_quote([bid()], [], cost=2.5)
        self.assertEqual((quote.kind, quote.price), (QUOTE_COST_COVERING, 2.5))

    def test_a_cost_quote_needs_a_buyer_with_money(self):
        quote = market_quote.no_trade_quote([bid(budget=0.0)], [], cost=2.5)
        self.assertIsNone(quote)

    def test_a_good_no_one_wants_and_no_one_offers_has_no_price_and_no_quote(self):
        result = goods_market.clear([], [], GOOD, AREA, "coin", LAST_PRICE)
        self.assertIsNone(result.traded_price)
        self.assertIsNone(result.quote)


class ImportBoundTests(unittest.TestCase):

    def test_an_import_is_at_most_what_the_partner_makes(self):
        self.assertEqual(import_tonnes_left(50.0, 500.0, 0.0), 50.0)

    def test_an_import_is_at_most_the_lift_the_carriers_have_left(self):
        self.assertEqual(import_tonnes_left(500.0, 30.0, 0.0), 30.0)

    def test_what_has_been_bought_this_year_comes_off_and_the_volume_is_never_negative(self):
        self.assertEqual(import_tonnes_left(50.0, 500.0, 20.0), 30.0)
        self.assertEqual(import_tonnes_left(50.0, 500.0, 80.0), 0.0)

    def test_an_unlimited_supply_and_lift_is_unlimited(self):
        self.assertEqual(import_tonnes_left(float("inf"), float("inf"), 5.0), float("inf"))


if __name__ == "__main__":
    unittest.main()
