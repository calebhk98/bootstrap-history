"""`goods_added_bids.AddedBids`: the columns of the bids later respend rounds add, against the `Bid` objects they replace.
`quantities_at` against `goods_market.quantity_at` of `bids()`, and `bids()` against the `Bid` the respend made."""
QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy.goods_added_bids import AddedBids
from sim.economy.goods_market import quantity_at
from sim.economy.goods_respend import RESPEND_PRIORITY
from sim.economy.types import Bid


def random_added(rng, count):
    return AddedBids("bread", "north", ["h%d" % each for each in range(count)], ["t%d" % rng.randint(0, 3) for _ in range(count)],
                     [rng.choice([0.0, rng.uniform(0.0, 40.0)]) for _ in range(count)], [rng.uniform(0.0, 5.0) for _ in range(count)],
                     [rng.choice([0.5, 1.0, 2.0]) for _ in range(count)], [rng.choice([0.0, rng.uniform(1.0, 500.0)]) for _ in range(count)],
                     [rng.choice([math.inf, rng.uniform(0.5, 6.0)]) for _ in range(count)])


class AddedBidsAreTheirBids(unittest.TestCase):

    def test_quantities_are_quantity_at_of_the_bids_on_random_columns(self):
        for seed in range(40):
            rng = random.Random(seed)
            added = random_added(rng, rng.randint(0, 8))
            price = rng.uniform(0.1, 7.0)
            self.assertEqual(added.quantities_at(price), [quantity_at(bid, price) for bid in added.bids()], seed)

    def test_a_bid_is_a_respend_bid_with_no_floor(self):
        added = AddedBids("bread", "north", ["h1"], ["t2"], [3.0], [1.5], [2.0], [9.0], [4.0])
        self.assertEqual(added.bids(), [Bid("h1", "bread", "north", "t2", 0.0, 3.0, 1.5, 2.0, 9.0, RESPEND_PRIORITY, maximum_price=4.0)])
        self.assertEqual(len(added), 1)


if __name__ == "__main__":
    unittest.main()
