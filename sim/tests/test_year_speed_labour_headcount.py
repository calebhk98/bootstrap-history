"""Numba port, labour switching: a pair's headcount (`income_kernel.headcount`) is the `math.fsum` of its bands, and the kept
one (`counted_headcount`) is read once until the caller clears its flag; no game."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy as np

from sim.labour.market.income_kernel import counted_headcount, headcount


class Headcount(unittest.TestCase):

    def test_equals_fsum_of_the_bands_and_nothing_where_absent(self):
        rng = random.Random(2)
        people = np.array([[rng.uniform(0.0, 50.0) for _band in range(5)] for _pair in range(40)])
        present = np.array([rng.random() < 0.8 for _pair in range(40)])
        for row in range(40):
            self.assertEqual(headcount(people, present, row), math.fsum(people[row].tolist()) if present[row] else 0.0)

    def test_kept_until_cleared(self):
        people, present = np.array([[1.0, 2.0, 3.0]]), np.array([True])
        totals, counted = np.zeros(1), np.zeros(1, np.bool_)
        self.assertEqual(counted_headcount(people, present, totals, counted, 0), 6.0)
        people[0, 0] = 10.0
        self.assertEqual(counted_headcount(people, present, totals, counted, 0), 6.0)
        counted[0] = False
        self.assertEqual(counted_headcount(people, present, totals, counted, 0), 15.0)


if __name__ == "__main__":
    unittest.main()
