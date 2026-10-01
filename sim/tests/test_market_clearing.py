"""The year's market for a material: scarcity moves the price around long-run cost.

Pure tests of sim/world/market.py. A shortage lifts the year's price above
the long-run cost anchor, a glut lowers it (down to the cost of running
capacity that is already built), founder sales reach supply and displace the
society's own producers, and the society's capacity follows the price.
"""
import unittest

from sim.world import market


def conditions(**changes):
    base = dict(household_demand_at_anchor_tonnes=100.0, committed_demand_tonnes=0.0,
                society_capacity_tonnes=100.0, actor_supply_tonnes=0.0,
                founder_sales_tonnes=0.0, stock_tonnes=0.0,
                demand_price_elasticity=0.5, floor_ratio=0.4, ceiling_ratio=6.0)
    base.update(changes)
    return market.MarketConditions(**base)


class PriceMovesWithScarcityTests(unittest.TestCase):
    def test_balanced_market_clears_at_the_anchor(self):
        outcome = market.clear_market(conditions())
        self.assertAlmostEqual(outcome.price_ratio, 1.0, places=9)
        self.assertAlmostEqual(outcome.society_sales_tonnes, 100.0, places=6)
        self.assertAlmostEqual(outcome.unsold_tonnes, 0.0, places=6)

    def test_shortage_raises_price_above_long_run_cost(self):
        outcome = market.clear_market(conditions(society_capacity_tonnes=80.0))
        self.assertGreater(outcome.price_ratio, 1.2)
        self.assertLessEqual(outcome.price_ratio, 6.0)
        self.assertGreater(outcome.society_sales_tonnes, 80.0)

    def test_glut_lowers_price_below_long_run_cost(self):
        outcome = market.clear_market(conditions(society_capacity_tonnes=120.0))
        self.assertLess(outcome.price_ratio, 0.9)
        self.assertGreaterEqual(outcome.price_ratio, 0.4)

    def test_price_never_leaves_the_floor_and_ceiling(self):
        glut = market.clear_market(conditions(society_capacity_tonnes=1e6))
        self.assertAlmostEqual(glut.price_ratio, 0.4, places=9)
        self.assertGreater(glut.unsold_tonnes, 0.0)
        famine = market.clear_market(conditions(society_capacity_tonnes=1.0))
        self.assertAlmostEqual(famine.price_ratio, 6.0, places=9)
        self.assertGreater(famine.unmet_demand_tonnes, 0.0)

    def test_sunk_capital_is_not_in_the_short_run_floor(self):
        # The floor is below the anchor: capacity already built keeps selling
        # below the long-run cost, which includes paying the capital back.
        glut = market.clear_market(conditions(society_capacity_tonnes=1e6))
        self.assertLess(glut.price_ratio, 1.0)

    def test_stock_windfall_lowers_price_at_once(self):
        before = market.clear_market(conditions())
        after = market.clear_market(conditions(stock_tonnes=30.0))
        self.assertLess(after.price_ratio, before.price_ratio)

    def test_actor_supply_counts_as_supply(self):
        base = market.clear_market(conditions())
        more = market.clear_market(conditions(actor_supply_tonnes=20.0))
        self.assertLess(more.price_ratio, base.price_ratio)

    def test_committed_purchases_raise_price(self):
        base = market.clear_market(conditions())
        bought = market.clear_market(conditions(committed_demand_tonnes=15.0))
        self.assertGreater(bought.price_ratio, base.price_ratio)


class FounderSalesDisplaceSocietyTests(unittest.TestCase):
    def test_sales_reach_supply_and_lower_the_price(self):
        without = market.clear_market(conditions())
        with_sales = market.clear_market(conditions(founder_sales_tonnes=10.0))
        self.assertLess(with_sales.price_ratio, without.price_ratio)

    def test_society_producers_lose_sales_to_founder(self):
        # Above the floor a lower price draws in some extra demand, so the
        # displacement is partial but positive.
        displaced = market.society_sales_displaced_by_founder(
            conditions(society_capacity_tonnes=100.0, founder_sales_tonnes=10.0))
        self.assertGreater(displaced, 0.0)
        self.assertLessEqual(displaced, 10.0)

    def test_displacement_is_one_for_one_when_price_is_at_the_floor(self):
        displaced = market.society_sales_displaced_by_founder(
            conditions(society_capacity_tonnes=1000.0, founder_sales_tonnes=10.0))
        self.assertAlmostEqual(displaced, 10.0, places=6)

    def test_no_sales_displace_nothing(self):
        self.assertEqual(market.society_sales_displaced_by_founder(conditions()), 0.0)


class CapacityFollowsPriceTests(unittest.TestCase):
    def test_capacity_grows_when_price_is_above_cost(self):
        self.assertGreater(market.adjusted_capacity(100.0, 1.5), 100.0)

    def test_capacity_shrinks_when_price_is_below_cost(self):
        self.assertLess(market.adjusted_capacity(100.0, 0.6), 100.0)

    def test_capacity_is_unchanged_at_the_anchor(self):
        self.assertAlmostEqual(market.adjusted_capacity(100.0, 1.0), 100.0)

    def test_one_year_moves_capacity_by_a_bounded_step(self):
        self.assertLess(market.adjusted_capacity(100.0, 6.0), 100.0 * 1.5)
        self.assertGreater(market.adjusted_capacity(100.0, 0.4), 100.0 * 0.5)

    def test_a_shortage_fades_as_capacity_catches_up(self):
        capacity = 70.0
        prices = []
        for _year in range(40):
            outcome = market.clear_market(conditions(society_capacity_tonnes=capacity))
            prices.append(outcome.price_ratio)
            capacity = market.adjusted_capacity(capacity, outcome.price_ratio)
        self.assertGreater(prices[0], 1.5)
        self.assertLess(abs(prices[-1] - 1.0), 0.1)

    def test_stock_carries_the_unsold_surplus(self):
        outcome = market.clear_market(conditions(society_capacity_tonnes=1e6))
        self.assertAlmostEqual(
            market.stock_after_year(outcome), outcome.unsold_tonnes * market.STOCK_RETENTION,
            places=6)


if __name__ == "__main__":
    unittest.main()
