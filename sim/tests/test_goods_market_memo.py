"""A market's buyers remember what they computed for one book (what they buy at a price, what a crossing solve
found) so that many nearby books against them cost less; remembering gives the answers computing afresh gives."""

QUICK_TOPIC = True

import math
import random
import unittest

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
