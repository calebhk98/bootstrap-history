"""Clearing details (sim/economy/goods_market.py): a returned price respects the minimum-price floor, and a
book-edge agent such as the mint never trades with itself."""
import unittest

from sim.economy import goods_market
from sim.economy.types import EDGE_MINT, Bid, Offer


class FloorTests(unittest.TestCase):
    def test_a_price_with_no_demand_is_not_below_the_minimum_price(self):
        offers = [Offer("seller", "slag", "area", "t1", 5.0, -2.0)]
        bids = [Bid("buyer", "slag", "area", "t1", 0.0, 0.0, 10.0, 1.0, 100.0)]
        result = goods_market.clear(bids, offers, "slag", "area", "coin", None)
        self.assertGreater(result.price, 0.0)


class SelfTradeTests(unittest.TestCase):
    def test_the_mint_does_not_clear_against_its_own_quote(self):
        offers = [Offer(EDGE_MINT, "silver", "area", "t1", 5.0, 100.0)]
        bids = [Bid(EDGE_MINT, "silver", "area", "t2", 0.0, 8.0, 100.0, 0.0, float("inf"), 9, maximum_price=100.0)]
        result = goods_market.clear(bids, offers, "silver", "area", "coin", 100.0)
        self.assertEqual(result.quantity, 0.0)
        self.assertEqual(result.fills, ())

    def test_another_buyer_still_takes_the_mints_metal(self):
        offers = [Offer(EDGE_MINT, "silver", "area", "t1", 5.0, 100.0)]
        bids = [Bid(EDGE_MINT, "silver", "area", "t2", 0.0, 8.0, 100.0, 0.0, float("inf"), 9, maximum_price=100.0),
                Bid("smith", "silver", "area", "t1", 3.0, 0.0, 100.0, 0.0, 1000.0)]
        result = goods_market.clear(bids, offers, "silver", "area", "coin", 100.0)
        self.assertAlmostEqual(result.quantity, 3.0)
        self.assertEqual({fill.agent for fill in result.fills}, {"smith", EDGE_MINT})


if __name__ == "__main__":
    unittest.main()
