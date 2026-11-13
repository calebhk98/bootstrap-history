"""`settled_rate`: the base rate moves from last year's toward the target by the declared share of the gap, except that it is never below the lowest ask a borrower would pay."""

QUICK_TOPIC = True

import unittest

import numpy

from sim.economy import credit
from sim.loans.clearing_kernel import settled_rate
from sim.loans.risk_kernel import ADJUSTMENT_SHARE


def constants():
    values = numpy.zeros(8)
    values[ADJUSTMENT_SHARE] = credit.RATE_ADJUSTMENT_SHARE_PER_YEAR
    return values


class SettledRate(unittest.TestCase):
    def test_a_rate_below_the_target_moves_only_the_declared_share(self):
        moved = settled_rate(0.10, True, 0.20, 0.05, 0.50, constants())
        self.assertAlmostEqual(moved, 0.10 + credit.RATE_ADJUSTMENT_SHARE_PER_YEAR * (0.20 - 0.10))

    def test_a_rate_above_the_target_moves_only_the_declared_share(self):
        moved = settled_rate(0.20, True, 0.10, 0.05, 0.50, constants())
        self.assertAlmostEqual(moved, 0.20 + credit.RATE_ADJUSTMENT_SHARE_PER_YEAR * (0.10 - 0.20))

    def test_a_rate_far_below_the_target_moves_only_the_declared_share(self):
        moved = settled_rate(0.02, True, 0.10, 0.01, 0.50, constants())
        self.assertAlmostEqual(moved, 0.02 + credit.RATE_ADJUSTMENT_SHARE_PER_YEAR * (0.10 - 0.02))

    def test_with_no_last_rate_it_is_the_target(self):
        self.assertEqual(settled_rate(0.0, False, 0.2, 0.05, 0.50, constants()), 0.2)

    def test_a_rate_below_every_ask_that_a_borrower_would_pay_is_the_lowest_ask(self):
        self.assertEqual(settled_rate(0.01, True, 0.02, 0.05, 0.50, constants()), 0.05)

    def test_a_rate_below_every_ask_stays_partial_when_no_borrower_reaches_the_ask(self):
        moved = settled_rate(0.01, True, 0.02, 0.05, 0.04, constants())
        self.assertAlmostEqual(moved, 0.01 + credit.RATE_ADJUSTMENT_SHARE_PER_YEAR * (0.02 - 0.01))

    def test_a_rate_above_the_lowest_ask_is_not_pulled_to_it(self):
        moved = settled_rate(0.06, True, 0.30, 0.05, 0.50, constants())
        self.assertAlmostEqual(moved, 0.06 + credit.RATE_ADJUSTMENT_SHARE_PER_YEAR * (0.30 - 0.06))


if __name__ == "__main__":
    unittest.main()
