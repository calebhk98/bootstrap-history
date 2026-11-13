"""The base rate is where the funds lenders offer meet the funds borrowers request: the crossing of the two cumulative curves,
each drawn straight between its points, so it moves smoothly as one lender or borrower changes."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit_rate
from sim.economy.order_book import supply_demand_crossing


class CrossingTests(unittest.TestCase):
    def test_demand_beyond_the_cheap_lender_lands_between_the_asks_in_proportion(self):
        floors = [(0.01, 50.0), (0.10, 1000.0)]
        caps = [(0.30, 500.0)]
        self.assertAlmostEqual(supply_demand_crossing(floors, caps), 0.01 + 0.09 * (500.0 - 50.0) / 1000.0)

    def test_a_queue_for_one_lenders_funds_pays_that_lenders_ask_not_a_borrowers_cap(self):
        floors = [(0.05, 100.0)]
        caps = [(0.40, 50.0), (0.30, 1000.0)]
        self.assertAlmostEqual(supply_demand_crossing(floors, caps), 0.05)

    def test_a_queue_beyond_every_ask_stays_at_the_dearest_ask_however_high_the_caps(self):
        floors = [(0.01, 50.0), (0.10, 50.0)]
        self.assertAlmostEqual(supply_demand_crossing(floors, [(5.0, 1000.0)]), 0.10)

    def test_a_glut_of_funds_clears_at_the_lowest_ask(self):
        floors = [(0.01, 1000.0), (0.10, 1000.0)]
        caps = [(0.30, 100.0)]
        self.assertAlmostEqual(supply_demand_crossing(floors, caps), 0.01)

    def test_the_crossing_moves_continuously_with_a_lenders_ask(self):
        caps = [(0.30, 500.0)]
        before = supply_demand_crossing([(0.01, 50.0), (0.1000, 1000.0)], caps)
        after = supply_demand_crossing([(0.01, 50.0), (0.1001, 1000.0)], caps)
        self.assertLess(abs(after - before), 0.0001)

    def test_a_lender_of_a_negligible_sum_moves_the_rate_negligibly(self):
        caps = [(0.50, 150.0)]      # demand the other lenders can fund
        alone = supply_demand_crossing([(0.05, 100.0), (0.40, 100.0)], caps)
        with_dust = supply_demand_crossing([(0.05, 100.0), (0.40, 100.0), (0.45, 0.5)], caps)
        self.assertLess(abs(with_dust - alone), 0.001)

    def test_with_no_lenders_or_no_borrowers_it_is_the_one_sides_best_limit(self):
        self.assertIsNone(credit_rate.base_rate_target([], []))
        self.assertAlmostEqual(credit_rate.base_rate_target([(0.05, 10.0), (0.03, 10.0)], []), 0.03)
        self.assertAlmostEqual(credit_rate.base_rate_target([], [(0.2, 10.0), (0.3, 10.0)]), 0.3)

    def test_the_target_is_the_crossing(self):
        floors, caps = [(0.01, 50.0), (0.10, 1000.0)], [(0.30, 500.0)]
        self.assertEqual(credit_rate.base_rate_target(floors, caps), supply_demand_crossing(floors, caps))


if __name__ == "__main__":
    unittest.main()
