"""`market_column_kernels.traded_price_by_group` on written-out groups: the weighted price is the exact (`math.fsum`) figure, a group with
no weight takes the price of its first kept place, and a group with no kept place has none."""

QUICK_TOPIC = True

import math
import unittest

import numpy

from sim.economy.market_column_kernels import traded_price_by_group


class TradedPriceByGroup(unittest.TestCase):
    def test_a_group_with_weight_is_the_weighted_mean_summed_exactly(self):
        price = numpy.array([0.1, 0.2, 0.3, 1e16, 1.0, -1e16])
        weight = numpy.array([1.0, 2.0, 3.0, 1.0, 1.0, 1.0])
        values, exists = traded_price_by_group(numpy.array([3, 6]), numpy.ones(6, dtype=bool), price, weight)
        self.assertEqual(values[0], math.fsum(price[:3] * weight[:3]) / math.fsum(weight[:3]))
        self.assertEqual(values[1], math.fsum(price[3:] * weight[3:]) / math.fsum(weight[3:]))
        self.assertTrue(exists.all())

    def test_a_group_with_no_weight_takes_the_price_of_its_first_kept_place(self):
        kept = numpy.array([False, True, True])
        values, exists = traded_price_by_group(numpy.array([3]), kept, numpy.array([5.0, 7.0, 9.0]), numpy.zeros(3))
        self.assertEqual(values[0], 7.0)
        self.assertTrue(exists[0])

    def test_a_group_with_no_kept_place_has_no_price(self):
        values, exists = traded_price_by_group(numpy.array([2, 3]), numpy.array([False, False, True]), numpy.array([5.0, 7.0, 9.0]),
                                               numpy.array([0.0, 0.0, 1.0]))
        self.assertEqual(exists.tolist(), [False, True])
        self.assertEqual(values[1], 9.0)

    def test_no_groups_is_empty(self):
        values, exists = traded_price_by_group(numpy.empty(0, dtype=numpy.int64), numpy.empty(0, dtype=bool), numpy.empty(0), numpy.empty(0))
        self.assertEqual((len(values), len(exists)), (0, 0))


if __name__ == "__main__":
    unittest.main()
