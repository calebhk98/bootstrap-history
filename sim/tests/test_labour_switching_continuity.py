"""Switching's choice is continuous in the scores: a destination a hair worse than staying weighs a hair less than one a hair
better, never nothing, and no share jumps as a destination crosses the negligible cutoff or an income crosses a threshold.
Each test calls one function (`band_shares`, `plan_area`); no game."""

QUICK_TOPIC = True

import unittest

import numpy as np

from sim.labour.market import switching_kernel
from sim.labour.market.switching_discounts import discount_tables

NEGLIGIBLE = 1e-3


def shares_of(scores, stay_score):
    """`band_shares` for one band whose targets score `scores`: (shares, moves)."""
    count = len(scores)
    shares, moves = np.zeros((1, count)), np.zeros(1, np.bool_)
    switching_kernel.band_shares(np.array([scores], dtype=float), np.arange(count), count, stay_score, 1.0, NEGLIGIBLE, shares,
                                 moves, np.empty(count))
    return shares[0], bool(moves[0])


class BandSharesAreContinuous(unittest.TestCase):

    def test_an_established_worker_weighs_a_target_just_under_staying(self):
        under, moves_under = shares_of([-1e-9], 0.0)
        over, moves_over = shares_of([1e-9], 0.0)
        self.assertTrue(moves_under)
        self.assertGreater(under[0], 0.0)
        self.assertAlmostEqual(under[0], over[0], delta=1e-8)
        self.assertTrue(moves_over)

    def test_no_share_jumps_as_a_target_crosses_the_negligible_cutoff(self):
        previous = None
        for step in range(1500):
            score = -5.5 + step * 1e-3         # the weak target's share passes the cutoff near -4.8
            shares, _ = shares_of([2.0, score], 0.0)
            if previous is not None:
                for one, before in zip(shares.tolist(), previous):
                    self.assertAlmostEqual(one, before, delta=1e-5)
            previous = shares.tolist()

    def test_a_lone_target_fading_under_the_cutoff_takes_its_share_to_zero(self):
        previous = None
        for step in range(2000):
            shares, _ = shares_of([-6.0 - step * 1e-3], 0.0)
            if previous is not None:
                self.assertAlmostEqual(shares[0], previous, delta=1e-5)
            previous = shares[0]
        self.assertEqual(previous, 0.0)

    def test_no_target_weighs_more_than_staying_leaves_it(self):
        shares, _ = shares_of([3.0, 2.0, 1.0, -1.0], 0.5)
        self.assertLessEqual(float(shares.sum()), 1.0)


def planned_share(later, vacancy=False):
    """The share of the one band of one established source that `plan_area` sends to the only destination, income after
    training `later`, the source earning 300 and the unit of score 300."""
    income, baseline, subsistence = np.array([300.0]), 300.0, 300.0
    years = np.array([2.0, 0.0])
    discounts = discount_tables(0.03, 40.0, 0.5, years, 0.3)
    shares = np.zeros((1, 2, 1, 2))
    plan_area_arguments = (np.array([[100.0]]), income, np.array([0.0]), baseline, np.array([300.0, later]), np.array([False, vacancy]),
                           np.array([[1.0], [1.0]]), discounts, np.zeros((1, 2), np.bool_), np.array([0], np.int64), np.array([False]), 0,
                           subsistence, 0.03, 40.0, 0.05, 0.5)
    switching_kernel.plan_area(*plan_area_arguments, 1.0, NEGLIGIBLE, np.zeros((1, 2), np.bool_), np.zeros((1, 2, 2)),
                               np.zeros((1, 2, 2), np.bool_), shares, np.zeros((1, 2, 1), np.bool_), np.zeros((1, 2), np.bool_),
                               np.zeros((1, 2)))
    return float(shares[0, 0, 0, 1])


class PlannedSharesAreContinuous(unittest.TestCase):

    def test_a_destination_paying_a_hair_less_than_staying_gets_nearly_the_share_of_one_paying_a_hair_more(self):
        under, over = planned_share(300.0 - 1e-6), planned_share(300.0 + 1e-6)
        self.assertGreater(under, 0.0)
        self.assertAlmostEqual(under, over, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
