"""Where borrowers queue for scarce funds, the base rate is what the lenders who lend ask, not what the last borrower
in the queue would pay: lenders price the loan (their ask plus the borrower's premium) and ration by quantity."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit_rate
from sim.economy.labour import clearing_point


class QueueRateTests(unittest.TestCase):
    def test_a_queue_for_one_lenders_funds_pays_that_lenders_ask_not_the_last_bidders_cap(self):
        floors = [(0.05, 100.0)]
        caps = [(0.40, 50.0), (0.30, 1000.0)]
        self.assertAlmostEqual(clearing_point(floors, caps), 0.30)      # the borrowers' price, for contrast
        self.assertAlmostEqual(credit_rate.base_rate_target(floors, caps), 0.05)

    def test_the_rate_is_the_dearest_ask_among_lenders_who_are_lending(self):
        floors = [(0.05, 100.0), (0.10, 100.0), (0.60, 100.0)]
        caps = [(0.50, 1000.0)]
        self.assertAlmostEqual(credit_rate.base_rate_target(floors, caps), 0.10)

    def test_a_lender_of_a_negligible_sum_does_not_set_the_rate(self):
        floors = [(0.05, 100.0), (0.40, 0.5)]
        caps = [(0.50, 1000.0)]
        self.assertAlmostEqual(credit_rate.base_rate_target(floors, caps), 0.05)

    def test_a_glut_of_funds_still_clears_at_the_lenders_floor(self):
        floors = [(0.01, 1000.0), (0.10, 1000.0)]
        caps = [(0.30, 100.0)]
        self.assertAlmostEqual(credit_rate.base_rate_target(floors, caps), clearing_point(floors, caps))
        self.assertAlmostEqual(credit_rate.base_rate_target(floors, caps), 0.01)

    def test_demand_beyond_the_cheap_lender_reaches_the_dearer_lenders_ask(self):
        floors = [(0.01, 50.0), (0.10, 1000.0)]
        caps = [(0.30, 500.0)]
        self.assertAlmostEqual(credit_rate.base_rate_target(floors, caps), 0.10)

    def test_with_no_lenders_or_no_borrowers_it_is_the_plain_clearing_point(self):
        self.assertIsNone(credit_rate.base_rate_target([], []))
        self.assertAlmostEqual(credit_rate.base_rate_target([(0.05, 10.0)], []), 0.05)
        self.assertAlmostEqual(credit_rate.base_rate_target([], [(0.2, 10.0)]), 0.2)


if __name__ == "__main__":
    unittest.main()
