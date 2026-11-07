"""Numba port, goods clearing: the arrays a market's bids are packed into for the kernels (`DemandArrays`) are the ones the
demand schedule of the same bids gives (`DemandSchedule.kernel_arrays`, `tier_bounds`), on random bids, including bids with
no budget, no flexible part, no reference price and ceilings. The arrays are exactly equal: both copy and select the bids'
numbers without arithmetic. No game."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy

from sim.economy.goods_market_demand import DemandArrays, DemandSchedule
from sim.economy.types import Bid


def random_bid(rng, index):
    budget = rng.choice([0.0, -1.0, rng.uniform(1.0, 500.0)])
    return Bid("b%d" % index, "grain", "area", "t1", rng.choice([0.0, rng.uniform(0.0, 20.0)]),
               rng.choice([0.0, rng.uniform(0.0, 20.0)]), rng.choice([0.0, rng.uniform(0.1, 9.0), rng.uniform(0.1, 9.0)]),
               rng.choice([0.0, rng.uniform(0.1, 2.0)]), budget, rng.choice([0, 0, 1, 2]),
               maximum_price=rng.choice([math.inf, math.inf, rng.uniform(0.5, 9.0)]))


class DemandArraysAgreeWithTheSchedule(unittest.TestCase):

    def test_random_bids(self):
        rng = random.Random(21)
        for _round in range(200):
            bids = sorted((random_bid(rng, index) for index in range(rng.randint(1, 12))), key=lambda bid: bid.priority)
            packed = DemandArrays(bids)
            schedule = DemandSchedule(bids)
            for ours, theirs in zip(packed.kernel_arrays()[:6], schedule.kernel_arrays()[:6]):
                numpy.testing.assert_array_equal(ours, theirs)
            self.assertEqual(packed.kernel_arrays()[6], schedule.kernel_arrays()[6])
            numpy.testing.assert_array_equal(packed.tier_bounds(), schedule.tier_bounds())


class CostFiguresAgreeWithTheTwoReads(unittest.TestCase):
    """`seller_offers.cost_figures` reads a producer's prices once for what `unit_cost` and `input_share_of_cost` read twice."""

    def test_a_producer_and_a_seller_that_is_not_one(self):
        from sim.tests.test_economy_ask_band import game, View, GOOD, TILE
        from sim.economy import seller_offers
        from sim.economy.types import Offer
        setup, record = game("maker")
        view = View()
        for seller in ("maker", "stranger"):
            offer = Offer(seller, GOOD, "area", TILE, 5.0, 4.0)
            cost, share = seller_offers.cost_figures(setup, record, view, offer)
            self.assertEqual(cost, seller_offers.unit_cost(setup, record, view, offer))
            self.assertEqual(share, seller_offers.input_share_of_cost(setup, record, view, offer))


if __name__ == "__main__":
    unittest.main()
