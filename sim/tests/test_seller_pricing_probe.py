"""The shortcut for clearing one market many times against the same buyers (buyers sorted once, no fills built) gives
exactly the price and quantity a full `goods_market.clear` gives."""

QUICK_TOPIC = True

import math
import random
import unittest
from dataclasses import replace

from sim.economy import goods_market
from sim.economy.types import Bid, Offer

GOOD, AREA = "cloth", "area"
SELLER = "producer:own"


def random_market(seed):
    """Buyers with floors, tiers and ceilings, several rivals (some sharing a reservation), and the seller's offer."""
    generator = random.Random(seed)
    bids = [Bid("household:%d" % index, GOOD, AREA, "tile%d" % (index % 3),
                generator.choice([0.0, generator.uniform(0.0, 5.0)]), generator.uniform(0.0, 50.0),
                generator.uniform(0.5, 2.0), generator.choice([0.5, 1.0, 1.5]), generator.uniform(0.0, 80.0),
                generator.choice([0, 0, 1]), generator.choice([math.inf, generator.uniform(0.8, 3.0)]))
            for index in range(generator.randint(0, 40))]
    asks = [generator.uniform(0.2, 2.5) for _ in range(4)]
    rivals = [Offer("producer:%d" % index, GOOD, AREA, "tile%d" % (index % 3),
                    generator.choice([0.0, generator.uniform(0.1, 40.0)]), generator.choice(asks + [-0.5]))
              for index in range(generator.randint(0, 8))]
    rivals.append(Offer(SELLER, GOOD, AREA, "tile9", generator.uniform(0.0, 5.0), generator.choice(asks)))
    offer = Offer(SELLER, GOOD, AREA, "tile0", generator.uniform(0.1, 60.0), generator.choice(asks))
    last_price = generator.choice([None, generator.uniform(0.3, 2.0)])
    return bids, rivals, offer, last_price


def by_full_clear(bids, rivals, offer, reservation, last_price):
    offers = list(rivals) + ([] if reservation is None else [replace(offer, reservation_price=reservation)])
    result = goods_market.clear(bids, offers, GOOD, AREA, "", last_price)
    sold = math.fsum(fill.quantity for fill in result.fills if fill.agent == offer.seller and fill.side == "sell")
    return result.price, sold


class ShortcutMatchesFullClear(unittest.TestCase):
    def test_price_and_sold_equal_a_full_clear_for_every_reservation(self):
        for seed in range(150):
            bids, rivals, offer, last_price = random_market(seed)
            buyers = goods_market.Buyers(bids, last_price)
            ordered = goods_market.in_clearing_order(rivals)
            for reservation in (None, 0.0, 0.4, 1.0, 1.7, 5.0):
                offers = ordered if reservation is None else goods_market.with_offer(
                    ordered, replace(offer, reservation_price=reservation))
                self.assertEqual(goods_market.price_and_sold(buyers, offers, SELLER),
                                 by_full_clear(bids, rivals, offer, reservation, last_price), (seed, reservation))


if __name__ == "__main__":
    unittest.main()
