"""`share_working` (sim/economy/producers.py): the share of a producer's workplaces its expected revenue covers, at the extremes
where the revenue is so small against the cost that their ratio is no longer a positive number."""
import math
import unittest

from sim.economy.producers import share_working, working_cost_ratio

QUICK_TOPIC = True


class ShareWorkingAtTheExtremes(unittest.TestCase):

    def test_a_revenue_too_small_to_compare_with_the_cost_keeps_no_workplace_working(self):
        self.assertEqual(share_working(1e-300, 1e300), 0.0)

    def test_an_endless_cost_keeps_no_workplace_working(self):
        self.assertEqual(share_working(5.0, math.inf), 0.0)

    def test_with_nothing_working_the_working_cost_is_the_producers_own(self):
        self.assertEqual(working_cost_ratio(1e-300, 1e300), 1.0)

    def test_an_ordinary_revenue_still_reads_the_spread_of_costs(self):
        self.assertTrue(0.0 < share_working(5.0, 5.0) < 1.0)


if __name__ == "__main__":
    unittest.main()
