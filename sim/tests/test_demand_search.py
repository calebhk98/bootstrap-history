"""Sellers that sell out with buyers turned away raise their asks within the year, the mirror of the unsold search: to the
highest common level at which they still sell out, which is where the money bid no longer buys what is offered, or where
the buyers' ceilings end. Written-out books."""

QUICK_TOPIC = True

import unittest

from sim.economy import demand_search, goods_market
from sim.economy.types import Bid, Offer

GOOD, AREA = "grain", "area"


def buyer(floor, budget, maximum=float("inf")):
    return Bid("buyer", GOOD, AREA, "tile", floor, 0.0, 1.0, 1.0, budget, 0, maximum)


def seller(name, quantity, ask):
    return Offer(name, GOOD, AREA, "tile", quantity, ask)


class RaiseAsksTests(unittest.TestCase):
    def test_asks_rise_until_the_money_bid_just_buys_the_stock(self):
        # 20 wanted at any price a budget of 100 can pay for: 10 units on offer stop selling out above 100 / 10
        buyers = goods_market.Buyers([buyer(20.0, 100.0)], None)
        offers = [seller("a", 5.0, 1.0), seller("b", 5.0, 1.0)]
        raised = demand_search.raise_asks(buyers, offers, [0, 1])
        for offer in raised:
            self.assertAlmostEqual(offer.reservation_price, 10.0, delta=0.01)

    def test_asks_stop_at_the_buyers_ceiling(self):
        buyers = goods_market.Buyers([buyer(20.0, 1000.0, maximum=3.0)], None)
        offers = [seller("a", 5.0, 1.0), seller("b", 5.0, 1.0)]
        raised = demand_search.raise_asks(buyers, offers, [0, 1])
        for offer in raised:
            self.assertAlmostEqual(offer.reservation_price, 3.0, delta=0.01)

    def test_a_seller_left_out_keeps_its_ask(self):
        buyers = goods_market.Buyers([buyer(20.0, 100.0)], None)
        offers = [seller("a", 5.0, 1.0), seller("b", 5.0, 1.0)]
        raised = demand_search.raise_asks(buyers, offers, [0])
        self.assertEqual(raised[1].reservation_price, 1.0)
        self.assertGreater(raised[0].reservation_price, 1.0)

    def test_dearer_asks_lift_cheaper_ones_to_one_level(self):
        buyers = goods_market.Buyers([buyer(20.0, 100.0)], None)
        offers = [seller("a", 5.0, 1.0), seller("b", 5.0, 2.0)]
        raised = demand_search.raise_asks(buyers, offers, [0, 1])
        self.assertAlmostEqual(raised[0].reservation_price, raised[1].reservation_price, delta=0.01)
        self.assertGreaterEqual(raised[0].reservation_price, 2.0)

    def test_asks_stop_at_each_sellers_limit(self):
        # the money would carry the level to 10, but one seller may ask 2 at most and the other 3
        buyers = goods_market.Buyers([buyer(20.0, 100.0)], None)
        offers = [seller("a", 5.0, 1.0), seller("b", 5.0, 1.0)]
        raised = demand_search.raise_asks(buyers, offers, [0, 1], {0: 2.0, 1: 3.0})
        self.assertAlmostEqual(raised[0].reservation_price, 2.0, delta=0.01)
        self.assertAlmostEqual(raised[1].reservation_price, 3.0, delta=0.01)

    def test_a_seller_asking_above_its_limit_is_not_pulled_down(self):
        buyers = goods_market.Buyers([buyer(20.0, 100.0)], None)
        offers = [seller("a", 5.0, 4.0), seller("b", 5.0, 1.0)]
        raised = demand_search.raise_asks(buyers, offers, [0, 1], {0: 2.0, 1: 3.0})
        self.assertEqual(raised[0].reservation_price, 4.0)
        self.assertAlmostEqual(raised[1].reservation_price, 3.0, delta=0.01)

    def test_no_excess_demand_leaves_the_asks(self):
        # the buyer wants 4 of the 10 on offer: nobody was turned away
        buyers = goods_market.Buyers([buyer(4.0, 100.0)], None)
        offers = [seller("a", 5.0, 1.0), seller("b", 5.0, 1.0)]
        self.assertEqual(demand_search.raise_asks(buyers, offers, [0, 1]), offers)


if __name__ == "__main__":
    unittest.main()
