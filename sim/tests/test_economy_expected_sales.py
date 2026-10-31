"""Demand a producer learns from: what it sold, plus its share of what buyers wanted and did not get when it sold out."""
import unittest

from sim.economy.expected_sales import demand_seen


class DemandSeenTest(unittest.TestCase):
    def test_sold_out_adds_its_share_of_unmet_demand(self):
        self.assertAlmostEqual(demand_seen(sold=10.0, left=0.0, market_sold=40.0, market_unmet=20.0), 15.0)

    def test_not_sold_out_ignores_unmet_demand(self):
        self.assertEqual(demand_seen(sold=10.0, left=3.0, market_sold=40.0, market_unmet=20.0), 10.0)

    def test_no_unmet_demand_gives_sales(self):
        self.assertEqual(demand_seen(sold=10.0, left=0.0, market_sold=40.0, market_unmet=0.0), 10.0)

    def test_a_market_that_sold_nothing_gives_no_share(self):
        self.assertEqual(demand_seen(sold=0.0, left=0.0, market_sold=0.0, market_unmet=5.0), 0.0)


if __name__ == "__main__":
    unittest.main()
