"""`goods_market_kernels.pack_demand` on a market with no bids: no tier and nothing written past its arrays (numba does
not check bounds, so a write past the end goes unseen in a compiled run)."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.economy import goods_market_kernels


class EmptyDemandTests(unittest.TestCase):
    def test_no_bids_pack_to_no_tier(self):
        packed = goods_market_kernels.pack_demand(numpy.zeros((0, 7)))
        self.assertEqual(list(packed[-1]), [0])
        self.assertTrue(all(len(column) == 0 for column in packed[:5]))

    def test_one_tier_ends_at_the_count(self):
        table = numpy.array([[1.0, 0.0, 1.0, 1.0, 5.0, numpy.inf, 0.0], [2.0, 0.0, 1.0, 1.0, 5.0, numpy.inf, 0.0]])
        self.assertEqual(list(goods_market_kernels.pack_demand(table)[-1]), [0, 2])


if __name__ == "__main__":
    unittest.main()
