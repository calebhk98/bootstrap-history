"""The unsold search reads what each seller sells without building fills (`goods_market.sold_by_seller`): the
figures equal the sums of the sell fills `goods_market.clear` gives for the same book, bit for bit."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy import goods_market
from sim.economy.types import Bid, Offer

GOOD, AREA, TILE = "grain", "area", "tile"


def market(generator):
    bids = [Bid("buyer%d" % index, GOOD, AREA, TILE, generator.choice([0.0, 2.0]), generator.uniform(0.0, 30.0),
                generator.uniform(0.5, 3.0), generator.uniform(0.3, 2.0), generator.uniform(5.0, 400.0),
                generator.choice([0, 1]), generator.choice([4.0, 1e9]))
            for index in range(generator.randint(1, 6))]
    offers = [Offer("seller%d" % index, GOOD, AREA, generator.choice(["tile", "other"]), generator.uniform(0.0, 40.0),
                    generator.choice([0.0, 0.7, 1.0, 1.0, 1.6, 2.5]))
              for index in range(generator.randint(0, 5))]
    return bids, offers


class SoldBySellerTests(unittest.TestCase):
    def test_equals_the_sell_fills_of_a_full_clear(self):
        generator = random.Random(7)
        for _case in range(300):
            bids, offers = market(generator)
            last_price = generator.choice([None, 1.2])
            result = goods_market.clear(bids, offers, GOOD, AREA, "coin", last_price)
            expected = {}
            for fill in result.fills:
                if fill.side == "sell":
                    key = (fill.agent, fill.tile)
                    expected[key] = expected.get(key, 0.0) + fill.quantity
            self.assertEqual(goods_market.sold_by_seller(goods_market.Buyers(bids, last_price), offers), expected)

    def test_clear_with_shared_buyers_equals_clear(self):
        generator = random.Random(11)
        for _case in range(100):
            bids, offers = market(generator)
            buyers = goods_market.Buyers(bids, 1.2)
            for _again in range(3):
                self.assertEqual(goods_market.clear(bids, offers, GOOD, AREA, "coin", 1.2, buyers),
                                 goods_market.clear(bids, offers, GOOD, AREA, "coin", 1.2))


if __name__ == "__main__":
    unittest.main()
