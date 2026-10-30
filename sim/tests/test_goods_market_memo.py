"""A market's buyers remember what they computed for one book (what they buy at a price, what a crossing solve
found) so that many nearby books against them cost less; remembering gives the answers computing afresh gives."""

QUICK_TOPIC = True

import math
import unittest
from dataclasses import replace

from sim.economy import goods_market
from sim.tests.test_seller_pricing_probe import SELLER, random_market


class BuyersMemory(unittest.TestCase):
    def test_traded_at_equals_rationing_the_wants_afresh(self):
        for seed in range(150):
            bids, _rivals, _offer, last_price = random_market(seed)
            buyers = goods_market.Buyers(bids, last_price)
            for price in (0.3, 0.9, 1.4, 2.5, 0.9, 0.3):
                for supply in (0.0, 1.0, 17.0, 1e6, 17.0):
                    wants = [goods_market.quantity_at(bid, price) for bid in buyers.bids]
                    expected = math.fsum(goods_market.ration(buyers.bids, wants, min(math.fsum(wants), supply)))
                    self.assertEqual(buyers.traded_at(price, supply), expected, (seed, price, supply))

    def test_books_cleared_one_after_another_match_books_cleared_on_fresh_buyers(self):
        for seed in range(100):
            bids, rivals, offer, last_price = random_market(seed)
            shared = goods_market.Buyers(bids, last_price)
            ordered = goods_market.in_clearing_order(rivals)
            for reservation in (0.4, 1.0, 1.7, 1.0001, 0.4, 3.0, 1.7):
                offers = goods_market.with_offer(ordered, replace(offer, reservation_price=reservation))
                fresh = goods_market.Buyers(bids, last_price)
                self.assertEqual(goods_market.price_and_sold(shared, offers, SELLER),
                                 goods_market.price_and_sold(fresh, offers, SELLER), (seed, reservation))
