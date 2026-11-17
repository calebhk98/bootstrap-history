"""Demand a producer learns from: what it sold, plus its capacity share of what buyers wanted and did not get when it sold out."""
QUICK_TOPIC = True

import unittest

from sim.economy.expected_sales import demand_seen, market_capacities


class DemandSeenTest(unittest.TestCase):
    def test_sold_out_adds_its_capacity_share_of_unmet_demand(self):
        self.assertAlmostEqual(demand_seen(sold=10.0, left=0.0, own_capacity=20.0, market_capacity=40.0, market_unmet=20.0), 20.0)

    def test_a_seller_that_sold_nothing_still_sees_its_share(self):
        self.assertAlmostEqual(demand_seen(sold=0.0, left=0.0, own_capacity=10.0, market_capacity=40.0, market_unmet=20.0), 5.0)

    def test_stock_left_comes_off_the_unmet_demand_it_counts(self):
        # its share of the unmet demand is 10; the 3 it still held could have served 3 of them
        self.assertAlmostEqual(demand_seen(sold=10.0, left=3.0, own_capacity=20.0, market_capacity=40.0, market_unmet=20.0), 17.0)

    def test_stock_left_at_or_above_its_share_of_the_unmet_demand_gives_sales(self):
        self.assertEqual(demand_seen(sold=10.0, left=10.0, own_capacity=20.0, market_capacity=40.0, market_unmet=20.0), 10.0)
        self.assertEqual(demand_seen(sold=10.0, left=25.0, own_capacity=20.0, market_capacity=40.0, market_unmet=20.0), 10.0)

    def test_a_hair_of_stock_left_moves_the_demand_seen_by_a_hair(self):
        # Complaint 473: a stock just over a rounding share of the sales dropped the whole unmet demand
        sold_out = demand_seen(sold=1000.0, left=0.0, own_capacity=20.0, market_capacity=40.0, market_unmet=400.0)
        a_hair_left = demand_seen(sold=1000.0, left=0.002, own_capacity=20.0, market_capacity=40.0, market_unmet=400.0)
        self.assertAlmostEqual(sold_out, 1200.0)
        self.assertAlmostEqual(a_hair_left, sold_out - 0.002)

    def test_no_unmet_demand_gives_sales(self):
        self.assertEqual(demand_seen(sold=10.0, left=0.0, own_capacity=20.0, market_capacity=40.0, market_unmet=0.0), 10.0)

    def test_a_seller_with_no_capacity_or_a_market_with_none_gives_sales(self):
        self.assertEqual(demand_seen(sold=3.0, left=0.0, own_capacity=0.0, market_capacity=40.0, market_unmet=5.0), 3.0)
        self.assertEqual(demand_seen(sold=0.0, left=0.0, own_capacity=0.0, market_capacity=0.0, market_unmet=5.0), 0.0)

    def test_the_shares_of_all_sellers_add_to_the_whole_unmet_demand(self):
        shares = [demand_seen(0.0, 0.0, capacity, 100.0, 30.0) for capacity in (50.0, 30.0, 20.0)]
        self.assertAlmostEqual(sum(shares), 30.0)


class MarketCapacitiesTest(unittest.TestCase):
    def test_capacity_is_summed_by_good_and_area(self):
        total = market_capacities([("a", {"bread": 2.0}, 10.0), ("b", {"bread": 2.0, "bran": 1.0}, 5.0), ("c", {"bread": 1.0}, 7.0)],
                                  lambda good, tile: "north" if tile in ("a", "b") else "south")
        self.assertEqual(total, {("bread", "north"): 30.0, ("bran", "north"): 5.0, ("bread", "south"): 7.0})


if __name__ == "__main__":
    unittest.main()
