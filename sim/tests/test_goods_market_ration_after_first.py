"""goods_market_ration.ration_after_first: the part of each want named first is served before the rest of it."""

QUICK_TOPIC = True

import unittest

from sim.economy.goods_market_ration import ration_after_first
from sim.economy.types import Bid


def bid(buyer, priority):
    return Bid(buyer, "silver_kg", "area", "tile", 0.0, 0.0, 1.0, 0.0, 1e9, priority)


class RationAfterFirst(unittest.TestCase):
    def setUp(self):
        # the mint is in the tier served first; it wants 100 at the price and nothing a hair above it
        self.bids = [bid("mint", -1), bid("household:a", 0), bid("household:b", 0)]
        self.wants = [100.0, 20.0, 10.0]
        self.first = [0.0, 20.0, 10.0]

    def test_the_first_parts_are_served_in_full_and_the_rest_shares_what_is_left(self):
        self.assertEqual(ration_after_first(self.bids, self.wants, self.first, 50.0), [20.0, 20.0, 10.0])

    def test_everything_is_served_where_there_is_enough(self):
        self.assertEqual(ration_after_first(self.bids, self.wants, self.first, 500.0), self.wants)

    def test_where_even_the_first_parts_do_not_fit_they_share_by_tier_and_the_rest_gets_nothing(self):
        served = ration_after_first(self.bids, self.wants, self.first, 15.0)
        self.assertEqual(served[0], 0.0)
        self.assertAlmostEqual(served[1], 15.0 * 20.0 / 30.0)
        self.assertAlmostEqual(served[2], 15.0 * 10.0 / 30.0)

    def test_a_first_part_larger_than_the_want_counts_as_the_want(self):
        self.assertEqual(ration_after_first(self.bids, [100.0, 20.0, 10.0], [0.0, 25.0, 10.0], 50.0), [20.0, 20.0, 10.0])

    def test_nothing_served_adds_up_to_more_than_is_available(self):
        for available in (0.0, 5.0, 30.0, 70.0, 130.0, 200.0):
            self.assertLessEqual(sum(ration_after_first(self.bids, self.wants, self.first, available)), available + 1e-9)


if __name__ == "__main__":
    unittest.main()
