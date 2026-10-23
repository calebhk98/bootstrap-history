"""`goods_market.Buyers` builds its demand schedule when a market with offers first reads it: a market with no
offer clears without one, and what `clear` gives is what an eagerly built schedule gives."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy import goods_market
from sim.economy.goods_market_demand import DemandSchedule
from sim.economy.types import Bid, Offer

GOOD, AREA = "grain", "area"


def bids_of(generator):
    return [Bid("buyer%d" % index, GOOD, AREA, "tile", generator.choice([0.0, 2.0]), generator.uniform(0.0, 30.0),
                generator.uniform(0.5, 3.0), generator.uniform(0.3, 2.0), generator.uniform(5.0, 400.0),
                generator.choice([0, 1]), generator.choice([4.0, 1e9]))
            for index in range(generator.randint(1, 6))]


class LazyScheduleTests(unittest.TestCase):
    def test_a_market_without_offers_builds_no_schedule(self):
        generator = random.Random(2)
        for _case in range(50):
            bids = bids_of(generator)
            buyers = goods_market.Buyers(bids, 1.0)
            for offers in ([], [Offer("seller", GOOD, AREA, "tile", 0.0, 1.0)]):
                result = goods_market.clear(bids, offers, GOOD, AREA, "coin", 1.0, buyers)
                self.assertEqual(result.quantity, 0.0)
            self.assertNotIn("schedule", vars(buyers))

    def test_the_schedule_is_the_eager_one(self):
        generator = random.Random(4)
        for _case in range(100):
            bids = bids_of(generator)
            buyers = goods_market.Buyers(bids, 1.0)
            eager = DemandSchedule(buyers.bids)
            for price in (0.3, 1.0, 2.5, 40.0):
                self.assertEqual(buyers.schedule.total_at(price), eager.total_at(price))
                self.assertEqual(buyers.schedule.each_at(price), eager.each_at(price))
            offers = [Offer("seller", GOOD, AREA, "tile", 7.0, 1.0)]
            self.assertEqual(goods_market.clear(bids, offers, GOOD, AREA, "coin", 1.0, buyers),
                             goods_market.clear(bids, offers, GOOD, AREA, "coin", 1.0))


if __name__ == "__main__":
    unittest.main()
