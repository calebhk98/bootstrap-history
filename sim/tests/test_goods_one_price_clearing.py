"""goods_clear_one_price: the price where supply meets demand, the supply at a price, and who bought from whom."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import goods_market
from sim.economy.fresh_supply import FreshCurve
from sim.economy.goods_clear_one_price import (bid_top_at, clearing_price, pairing_of, price_moved_from, price_where_supply_meets,
                                                supply_at, untraded_quote)
from sim.economy.stock_supply import StockCurve
from sim.economy.types import QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK, Bid, Fill, Offer


def demand_at(price):
    return 100.0 / price


def supply_at_price(price):
    return 10.0 * price


class PriceWhereSupplyMeets(unittest.TestCase):
    def test_the_price_is_where_the_two_schedules_cross(self):
        # 100 / price = 10 * price at price = sqrt(10)
        price = price_where_supply_meets(demand_at, supply_at_price, 0.5, 20.0)
        self.assertAlmostEqual(price, math.sqrt(10.0), places=6)

    def test_lowest_where_supply_covers_demand_there(self):
        self.assertEqual(price_where_supply_meets(demand_at, supply_at_price, 4.0, 20.0), 4.0)

    def test_highest_where_supply_falls_short_even_there(self):
        self.assertEqual(price_where_supply_meets(demand_at, supply_at_price, 0.5, 2.0), 2.0)


class SupplyAt(unittest.TestCase):
    def test_sums_the_curves_and_the_posted_offers_at_or_under_the_price(self):
        curve = StockCurve(Offer("producer:a", "grain_kg", "area", "tile", 10.0, 1.0), 4.0, 2.0)
        posted = [Offer("producer:b", "grain_kg", "area", "tile", 3.0, 1.5),
                  Offer("producer:c", "grain_kg", "area", "tile", 4.0, 2.0),
                  Offer("producer:d", "grain_kg", "area", "tile", 5.0, 2.5)]
        # at the content price the curve lets go 10 - 4; the offers reserved at 1.5 and 2.0 take it, the one at 2.5 does not
        self.assertAlmostEqual(supply_at(2.0, [curve], posted), (10.0 - 4.0) + 3.0 + 4.0)

    def test_nothing_on_the_market_supplies_nothing(self):
        self.assertEqual(supply_at(2.0, [], []), 0.0)


def budget_buyers(budget, wanted=1e9):
    """Buyers that take up to `wanted` units and spend no more than `budget`: at a price above budget over wanted they
    take budget over the price."""
    return goods_market.Buyers([Bid("household:a", "grain_kg", "area", "tile", wanted, 0.0, 1.0, 0.0, budget)], None)


class ClearingPrice(unittest.TestCase):
    def setUp(self):
        # held 10, target 4, content price 2: lets go nothing under about 1.37, six at 2, all ten from about 2.57
        self.curve = StockCurve(Offer("producer:a", "grain_kg", "area", "tile", 10.0, 1.0), 4.0, 2.0)

    def test_inside_the_curve_the_price_is_where_the_buyers_want_what_the_curve_lets_go(self):
        price = clearing_price(budget_buyers(12.0), [self.curve], [])
        self.assertAlmostEqual(price, 2.0, places=6)            # six units at two is the budget of twelve
        self.assertAlmostEqual(self.curve.supply_at(price), 12.0 / price, places=6)

    def test_where_buyers_want_more_than_everything_held_the_price_is_where_their_wants_fall_to_it(self):
        price = clearing_price(budget_buyers(1000.0), [self.curve], [])
        self.assertGreater(price, self.curve.highest_price)
        self.assertAlmostEqual(price, 1000.0 / 10.0, places=6)

    def test_a_good_that_cannot_be_kept_clears_under_its_expected_price_when_buyers_want_less_than_was_made(self):
        fresh = FreshCurve(Offer("producer:baker", "grain_kg", "area", "tile", 100.0, 0.0), 2.0)
        price = clearing_price(budget_buyers(1e9, wanted=80.0), [fresh], [])
        self.assertLess(price, 2.0)
        self.assertAlmostEqual(fresh.supply_at(price), 80.0, places=4)

    def test_a_good_that_cannot_be_kept_clears_at_its_expected_price_when_buyers_want_just_what_was_made(self):
        fresh = FreshCurve(Offer("producer:baker", "grain_kg", "area", "tile", 100.0, 0.0), 2.0)
        self.assertAlmostEqual(clearing_price(budget_buyers(200.0), [fresh], []), 2.0, places=6)

    def test_with_no_curve_the_price_is_where_the_buyers_meet_the_posted_offers(self):
        posted = [Offer("merchant:a", "grain_kg", "area", "tile", 5.0, 3.0)]
        self.assertAlmostEqual(clearing_price(budget_buyers(40.0), [], posted), 40.0 / 5.0, places=6)


class PriceMovedFrom(unittest.TestCase):
    def setUp(self):
        self.stock = StockCurve(Offer("producer:a", "grain_kg", "area", "tile", 30.0, 1.0), 4.0, 2.0)
        self.fresh = FreshCurve(Offer("producer:baker", "grain_kg", "area", "tile", 10.0, 0.0), 6.0)
        self.buyers = goods_market.Buyers([Bid("household:a", "grain_kg", "area", "tile", 5.0, 0.0, 9.0, 0.0, 100.0)], None)

    def test_last_years_price_where_the_market_has_one(self):
        self.assertEqual(price_moved_from(3.5, [self.stock, self.fresh], self.buyers), 3.5)

    def test_with_no_price_yet_the_mean_price_its_producers_are_content_at_by_the_units_each_holds(self):
        for no_price in (None, math.nan, 0.0):
            self.assertAlmostEqual(price_moved_from(no_price, [self.stock, self.fresh], self.buyers), (2.0 * 30.0 + 6.0 * 10.0) / 40.0)

    def test_with_no_price_and_no_producer_the_price_the_buyers_reckon_the_good_at(self):
        self.assertAlmostEqual(price_moved_from(None, [], self.buyers), 9.0)

    def test_none_where_nobody_names_a_price(self):
        self.assertIsNone(price_moved_from(None, [], goods_market.Buyers([], None)))


def topped_bid(buyer, top, budget=1e9):
    return Bid(buyer, "silver_kg", "area", "tile", 0.0, 50.0, top, 0.0, budget, 0, top)


class BidTopAt(unittest.TestCase):
    def test_a_bid_that_ends_a_hair_under_the_price_is_at_it(self):
        self.assertEqual(bid_top_at([topped_bid("edge:mint", 10.0)], 10.0 * (1.0 + 1e-13)), 10.0)

    def test_a_bid_that_ends_at_the_price_is_at_it(self):
        self.assertEqual(bid_top_at([topped_bid("edge:mint", 10.0)], 10.0), 10.0)

    def test_none_where_every_bid_ends_well_away_from_the_price(self):
        self.assertIsNone(bid_top_at([topped_bid("edge:mint", 10.0), topped_bid("household:a", 30.0)], 12.0))
        self.assertIsNone(bid_top_at([Bid("household:a", "silver_kg", "area", "tile", 5.0, 0.0, 9.0, 0.0, 100.0)], 12.0))

    def test_the_highest_of_several_at_the_price(self):
        self.assertEqual(bid_top_at([topped_bid("a", 10.0 * (1.0 - 1e-12)), topped_bid("b", 10.0)], 10.0 * (1.0 + 1e-13)), 10.0)

    def test_a_bid_with_no_money_behind_it_is_no_step(self):
        self.assertIsNone(bid_top_at([topped_bid("edge:mint", 10.0, budget=0.0)], 10.0))

    def test_the_search_stops_a_hair_above_a_bids_top_and_the_top_is_found_from_there(self):
        # the mint wants 50 at ten or less; the household wants five whatever the price; the curve lets go more than five
        # and less than fifty-five at ten, so the wants step from above the supply to under it at ten
        curve = StockCurve(Offer("producer:a", "silver_kg", "area", "tile", 30.0, 1.0), 4.0, 2.0)
        bids = [topped_bid("edge:mint", 10.0), Bid("household:a", "silver_kg", "area", "tile", 5.0, 0.0, 9.0, 0.0, 1e9)]
        buyers = goods_market.Buyers(bids, None)
        found = price_where_supply_meets(buyers.schedule.total_at, curve.supply_at, 1.0, 40.0)
        self.assertGreater(found, 10.0)
        self.assertEqual(bid_top_at(buyers.bids, found), 10.0)


class UntradedQuote(unittest.TestCase):
    def setUp(self):
        # holds 30 against a target of 4: lets go from well under its content price of two, down to its floor of 1.5
        self.stock = StockCurve(Offer("producer:a", "lard_kg", "area", "tile", 30.0, 1.5), 4.0, 2.0, 1.5)
        self.fresh = FreshCurve(Offer("producer:baker", "lard_kg", "area", "tile", 10.0, 0.0), 6.0)

    def test_with_nobody_bidding_the_least_a_seller_with_units_takes(self):
        quote = untraded_quote([], [self.stock, self.fresh], [])
        self.assertEqual(quote.kind, QUOTE_LOWEST_UNFILLED_ASK)
        self.assertAlmostEqual(quote.price, self.stock.lowest_price)

    def test_a_good_that_cannot_be_kept_asks_the_price_its_maker_expected(self):
        quote = untraded_quote([], [self.fresh], [])
        self.assertEqual((quote.kind, quote.price), (QUOTE_LOWEST_UNFILLED_ASK, 6.0))

    def test_a_posted_offer_under_the_curves_is_the_least(self):
        quote = untraded_quote([], [self.stock], [Offer("merchant:a", "lard_kg", "area", "tile", 3.0, 0.5)])
        self.assertEqual((quote.kind, quote.price), (QUOTE_LOWEST_UNFILLED_ASK, 0.5))

    def test_buyers_who_would_pay_the_ask_and_still_got_nothing_leave_the_ask_as_the_quote(self):
        # the year's price was held under the sellers' ask: the market heads for the ask, not for a making cost
        bids = [Bid("household:a", "lard_kg", "area", "tile", 5.0, 0.0, 9.0, 0.0, 100.0)]
        quote = untraded_quote(bids, [self.stock], [])
        self.assertEqual(quote.kind, QUOTE_LOWEST_UNFILLED_ASK)
        self.assertAlmostEqual(quote.price, self.stock.lowest_price)

    def test_buyers_who_top_out_under_the_ask_leave_the_ask_as_the_quote(self):
        # the good is still on offer at the ask: a quote of the buyers' bid would hide it from them for a year
        bids = [Bid("household:a", "lard_kg", "area", "tile", 5.0, 0.0, 1.0, 0.0, 100.0, 0, 1.2)]
        quote = untraded_quote(bids, [self.stock], [])
        self.assertEqual(quote.kind, QUOTE_LOWEST_UNFILLED_ASK)
        self.assertAlmostEqual(quote.price, self.stock.lowest_price)

    def test_with_no_seller_holding_a_unit_the_buyers_best_bid(self):
        empty = StockCurve(Offer("producer:a", "lard_kg", "area", "tile", 0.0, 1.5), 4.0, 2.0, 1.5)
        bids = [Bid("household:a", "lard_kg", "area", "tile", 5.0, 0.0, 1.0, 0.0, 100.0, 0, 1.2)]
        quote = untraded_quote(bids, [empty], [])
        self.assertEqual((quote.kind, quote.price), (QUOTE_BEST_UNFILLED_BID, 1.2))

    def test_a_seller_with_nothing_to_sell_asks_nothing(self):
        empty = StockCurve(Offer("producer:a", "lard_kg", "area", "tile", 0.0, 1.5), 4.0, 2.0, 1.5)
        self.assertIsNone(untraded_quote([], [empty], []))


def fill(agent, quantity, price, side):
    return Fill(agent, "grain_kg", "area", "tile", quantity, price, side)


class PairingOf(unittest.TestCase):
    def setUp(self):
        self.fills = [fill("buyer:1", 5.0, 2.0, "buy"), fill("buyer:2", 3.0, 2.0, "buy"), fill("buyer:3", 0.0, 2.0, "buy"),
                      fill("seller:1", 6.0, 1.8, "sell"), fill("seller:2", 2.0, 1.9, "sell"), fill("seller:3", 0.0, 1.7, "sell")]
        self.pairing = pairing_of(self.fills)

    def test_the_pairs_sum_to_the_quantity_bought(self):
        self.assertAlmostEqual(sum(self.pairing.quantity), 5.0 + 3.0)

    def test_each_buyers_pairs_sum_to_its_fill(self):
        for index, (agent, _tile) in enumerate(self.pairing.buyers):
            bought = sum(amount for amount, buyer in zip(self.pairing.quantity, self.pairing.buyer_index) if buyer == index)
            self.assertAlmostEqual(bought, {"buyer:1": 5.0, "buyer:2": 3.0}[agent])

    def test_each_sellers_pairs_sum_to_its_fill(self):
        for index, (agent, _tile) in enumerate(self.pairing.sellers):
            sold = sum(amount for amount, seller in zip(self.pairing.quantity, self.pairing.seller_index) if seller == index)
            self.assertAlmostEqual(sold, {"seller:1": 6.0, "seller:2": 2.0}[agent])

    def test_asks_are_the_sellers_fill_prices(self):
        self.assertEqual(self.pairing.asks, (1.8, 1.9))

    def test_zero_quantity_fills_are_left_out(self):
        self.assertEqual(self.pairing.buyers, (("buyer:1", "tile"), ("buyer:2", "tile")))
        self.assertEqual(self.pairing.sellers, (("seller:1", "tile"), ("seller:2", "tile")))

    def test_buyers_take_from_the_next_seller_with_units_left(self):
        self.assertEqual(self.pairing.buyer_index, (0, 1, 1))
        self.assertEqual(self.pairing.seller_index, (0, 0, 1))
        self.assertEqual(self.pairing.quantity, (5.0, 1.0, 2.0))

    def test_no_fills_pair_nothing(self):
        self.assertEqual(pairing_of([]).quantity, ())


if __name__ == "__main__":
    unittest.main()
