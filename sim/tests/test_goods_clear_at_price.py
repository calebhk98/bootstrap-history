"""goods_market.clear_at_price: one market traded at a price given to it, the long side going short."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy.goods_market import clear_at_price
from sim.economy.types import Bid, Offer

GOOD, AREA, TILE, MONEY = "pot_kg", "area", "tile", "coin"
PRICE = 2.0


def fixed_bid(buyer, quantity, priority=0, budget=1e9, maximum_price=math.inf):
    """A buyer that wants `quantity` whatever the price, while its budget and its highest price allow."""
    return Bid(buyer, GOOD, AREA, TILE, quantity, 0.0, PRICE, 0.0, budget, priority, maximum_price)


def offer(seller, quantity, reservation):
    return Offer(seller, GOOD, AREA, TILE, quantity, reservation)


def bought(result, agent):
    return sum(fill.quantity for fill in result.fills if fill.side == "buy" and fill.agent == agent)


def sold(result, agent):
    return sum(fill.quantity for fill in result.fills if fill.side == "sell" and fill.agent == agent)


def cleared(bids, offers, price=PRICE):
    return clear_at_price(bids, offers, GOOD, AREA, MONEY, price, None)


class BuyersWantMoreThanIsOffered(unittest.TestCase):
    def setUp(self):
        self.result = cleared([fixed_bid("household:needs", 60.0, priority=0), fixed_bid("household:first", 30.0, priority=1),
                               fixed_bid("household:second", 90.0, priority=1)], [offer("producer:potter", 100.0, 1.0)])

    def test_everything_offered_is_sold_at_the_price_given(self):
        self.assertAlmostEqual(self.result.quantity, 100.0)
        self.assertEqual(self.result.price, PRICE)
        self.assertTrue(all(fill.price == PRICE for fill in self.result.fills))

    def test_the_first_tier_is_served_in_full_and_the_next_shares_what_is_left_pro_rata(self):
        self.assertAlmostEqual(bought(self.result, "household:needs"), 60.0)
        self.assertAlmostEqual(bought(self.result, "household:first"), 40.0 * 30.0 / 120.0)
        self.assertAlmostEqual(bought(self.result, "household:second"), 40.0 * 90.0 / 120.0)

    def test_the_result_carries_what_was_wanted_and_offered(self):
        self.assertAlmostEqual(self.result.demand_at_price, 180.0)
        self.assertAlmostEqual(self.result.offered_at_price, 100.0)

    def test_the_buyers_pay_the_price_for_what_they_got_and_no_more(self):
        spent = sum(fill.quantity * fill.price for fill in self.result.fills if fill.side == "buy")
        self.assertAlmostEqual(spent, 100.0 * PRICE)


class MoreIsOfferedThanBuyersWant(unittest.TestCase):
    def setUp(self):
        self.result = cleared([fixed_bid("household:a", 50.0)], [offer("producer:cheap", 20.0, 1.0), offer("producer:one", 30.0, 1.5),
                                                              offer("producer:two", 90.0, 1.5), offer("producer:dear", 40.0, 2.5)])

    def test_the_buyers_are_served_in_full(self):
        self.assertAlmostEqual(self.result.quantity, 50.0)
        self.assertAlmostEqual(bought(self.result, "household:a"), 50.0)

    def test_the_lowest_reservation_sells_first_and_the_marginal_group_pro_rata(self):
        self.assertAlmostEqual(sold(self.result, "producer:cheap"), 20.0)
        self.assertAlmostEqual(sold(self.result, "producer:one"), 30.0 * 30.0 / 120.0)
        self.assertAlmostEqual(sold(self.result, "producer:two"), 30.0 * 90.0 / 120.0)

    def test_an_offer_reserved_above_the_price_sells_nothing_and_is_not_counted_as_offered(self):
        self.assertEqual(sold(self.result, "producer:dear"), 0.0)
        self.assertAlmostEqual(self.result.offered_at_price, 20.0 + 30.0 + 90.0)


class NothingTrades(unittest.TestCase):
    def test_no_offer_takes_the_price(self):
        result = cleared([fixed_bid("household:a", 50.0)], [offer("producer:dear", 40.0, 2.5)])
        self.assertEqual((result.quantity, result.fills, result.price), (0.0, (), PRICE))

    def test_no_buyer_pays_the_price(self):
        result = cleared([fixed_bid("household:a", 50.0, maximum_price=1.0)], [offer("producer:a", 40.0, 1.5)])
        self.assertEqual((result.quantity, result.fills, result.price), (0.0, (), PRICE))
        self.assertAlmostEqual(result.offered_at_price, 40.0)

    def test_a_budget_caps_what_a_buyer_takes_at_the_price(self):
        result = cleared([fixed_bid("household:a", 50.0, budget=30.0)], [offer("producer:a", 40.0, 1.5)])
        self.assertAlmostEqual(result.quantity, 30.0 / PRICE)


if __name__ == "__main__":
    unittest.main()
