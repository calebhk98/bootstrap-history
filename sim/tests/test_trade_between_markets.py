"""Two economies' markets for one material, linked by freight (Complaints/109).

Pure tests of sim/world/trade_between.py. Goods move from the cheaper market
to the dearer one while the price gap exceeds the freight over the route, so
imports cap a home shortage and exports lift the price abroad.
"""

QUICK_TOPIC = True

import unittest

from sim.world import market, trade_between


def conditions(**changes):
    base = dict(household_demand_at_anchor_tonnes=100.0, committed_demand_tonnes=0.0,
                society_capacity_tonnes=100.0, actor_supply_tonnes=0.0,
                founder_sales_tonnes=0.0, stock_tonnes=0.0)
    base.update(changes)
    return market.MarketConditions(**base)


def trade(home, foreign, home_price=100.0, foreign_price=100.0, freight=10.0):
    return trade_between.clear_trading_markets(home, foreign, home_price, foreign_price, freight)


class FlowTests(unittest.TestCase):
    def test_balanced_markets_trade_nothing(self):
        outcome = trade(conditions(), conditions())
        self.assertEqual(outcome.flow_tonnes, 0.0)

    def test_a_gap_below_freight_moves_nothing(self):
        outcome = trade(conditions(), conditions(), home_price=100.0, foreign_price=95.0,
                        freight=10.0)
        self.assertEqual(outcome.flow_tonnes, 0.0)

    def test_a_home_shortage_draws_imports(self):
        home = conditions(society_capacity_tonnes=60.0)
        alone = market.clear_market(home)
        outcome = trade(home, conditions())
        self.assertGreater(outcome.flow_tonnes, 0.0)
        self.assertLess(outcome.home.price_ratio, alone.price_ratio)

    def test_imports_stop_where_the_gap_equals_freight(self):
        home = conditions(society_capacity_tonnes=60.0)
        outcome = trade(home, conditions(), freight=10.0)
        gap = 100.0 * outcome.home.price_ratio - 100.0 * outcome.foreign.price_ratio
        self.assertAlmostEqual(gap, 10.0, places=3)

    def test_dearer_freight_means_less_import_and_a_higher_home_price(self):
        home = conditions(society_capacity_tonnes=60.0)
        near = trade(home, conditions(), freight=5.0)
        far = trade(home, conditions(), freight=40.0)
        self.assertGreater(near.flow_tonnes, far.flow_tonnes)
        self.assertLess(near.home.price_ratio, far.home.price_ratio)

    def test_imports_raise_the_price_abroad(self):
        home = conditions(society_capacity_tonnes=60.0)
        outcome = trade(home, conditions())
        self.assertGreater(outcome.foreign.price_ratio, market.clear_market(conditions()).price_ratio)

    def test_a_foreign_shortage_draws_exports_from_home(self):
        foreign = conditions(society_capacity_tonnes=60.0)
        outcome = trade(conditions(), foreign)
        self.assertLess(outcome.flow_tonnes, 0.0)
        self.assertGreater(outcome.home.price_ratio, 1.0)

    def test_a_cheaper_foreign_producer_undercuts_home(self):
        outcome = trade(conditions(), conditions(), home_price=100.0, foreign_price=50.0,
                        freight=10.0)
        self.assertGreater(outcome.flow_tonnes, 0.0)

    def test_the_founders_sales_count_in_the_trading_market(self):
        home = conditions(founder_sales_tonnes=30.0)
        self.assertLess(trade(home, conditions(), home_price=100.0, foreign_price=100.0,
                              freight=1.0).home.price_ratio,
                        market.clear_market(conditions()).price_ratio)

    def test_a_market_that_cannot_supply_sends_nothing(self):
        outcome = trade(conditions(society_capacity_tonnes=60.0),
                        conditions(society_capacity_tonnes=0.0, household_demand_at_anchor_tonnes=0.0))
        self.assertEqual(outcome.flow_tonnes, 0.0)

    def test_an_unpriced_foreign_good_is_not_traded(self):
        outcome = trade(conditions(society_capacity_tonnes=60.0), conditions(), foreign_price=0.0)
        self.assertEqual(outcome.flow_tonnes, 0.0)


if __name__ == "__main__":
    unittest.main()
