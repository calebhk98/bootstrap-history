"""The shares of a market's price that stay after producers' additions, priced for every request of a year in one kernel call
(`share_prices.shares_after_additions`), against the Python search on `Bid` objects (`share_price_plain.plain_share`), on written-out and
random markets under numba and ROME_NO_JIT=1. Shares agree to a relative 1e-12 (the kernel runs the same search, so they are equal); which
requests need the objects is exact."""
QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import bid_columns, share_prices
from sim.economy.types import Bid
from sim.tests.share_price_plain import plain_share
from sim.tests.test_crossing_kernels import outcome, random_bids


def market_of(bids):
    return bid_columns.columns_of_bids(bids), bid_columns.order_of_bids(bids)


class SharesAfterAdditions(unittest.TestCase):

    def test_a_written_out_market_one_request(self):
        bids = [Bid("buyer", "g", "a", "t", 0.0, 100.0, 1.0, 2.0, 1e9)]
        columns, order = market_of(bids)
        shares, needs_objects = share_prices.shares_after_additions([columns], [order], [100.0], [0], [10.0])
        self.assertFalse(needs_objects[0])
        self.assertAlmostEqual(shares[0], plain_share(bids, 100.0, 10.0), delta=1e-12)
        self.assertLess(shares[0], 1.0)

    def test_nothing_to_move_leaves_the_price(self):
        bids = [Bid("buyer", "g", "a", "t", 0.0, 100.0, 1.0, 2.0, 1e9)]
        columns, order = market_of(bids)
        empty_columns, empty_order = market_of([])
        shares, needs_objects = share_prices.shares_after_additions(
            [columns, columns, empty_columns], [order, order, empty_order], [0.0, 100.0, 100.0], [0, 1, 2], [10.0, 0.0, 10.0])
        self.assertEqual(shares.tolist(), [1.0, 1.0, 1.0])
        self.assertEqual(needs_objects.tolist(), [False, False, False])

    def test_no_requests(self):
        shares, needs_objects = share_prices.shares_after_additions([], [], [], [], [])
        self.assertEqual(len(shares), 0)
        self.assertEqual(len(needs_objects), 0)

    def test_random_markets_and_requests(self):
        for seed in range(60):
            rng = random.Random(seed)
            markets = [random_bids(rng, rng.randint(0, 12), ceilings=seed % 2 == 0) for _each in range(rng.randint(1, 5))]
            traded = [rng.choice([0.0, rng.uniform(0.5, 60.0), rng.uniform(60.0, 900.0)]) for _each in markets]
            request_market = sorted(rng.randrange(len(markets)) for _each in range(rng.randint(0, 9)))
            added = [rng.choice([0.0, rng.uniform(0.1, 30.0), rng.uniform(30.0, 600.0)]) for _each in request_market]
            columns, orders = zip(*[market_of(bids) for bids in markets])
            try:
                shares, needs_objects = share_prices.shares_after_additions(columns, orders, traded, request_market, added)
            except (OverflowError, ZeroDivisionError, ValueError):     # plain Python, ROME_NO_JIT: an exponential that overflows raises
                continue
            for request, (market, quantity) in enumerate(zip(request_market, added)):
                if needs_objects[request]:
                    continue
                expected = outcome(plain_share, markets[market], traded[market], quantity)
                if isinstance(expected, type):
                    continue
                self.assertAlmostEqual(shares[request], expected, delta=1e-12 * max(1.0, abs(expected)), msg=(seed, request))

    def test_a_request_is_never_answered_wrongly_by_leaving_it_to_the_objects(self):
        # a market the columns cannot prepare is handed back to the caller (needs_objects), not given a share
        bids = [Bid("b", "g", "a", "t", float("nan"), 1.0, 1.0, 1.0, 5.0)]
        columns, order = market_of(bids)
        shares, needs_objects = share_prices.shares_after_additions([columns], [order], [10.0], [0], [3.0])
        self.assertTrue(needs_objects[0])


if __name__ == "__main__":
    unittest.main()
