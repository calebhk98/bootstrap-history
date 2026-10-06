"""Merchants have a cost and a response: a thin gap does not move goods (Complaints/339)."""

QUICK_TOPIC = True

import math
import unittest

from sim.world import market, trade_between, trader_response


def conditions(**changes):
    base = dict(household_demand_at_anchor_tonnes=100.0, committed_demand_tonnes=0.0,
                society_capacity_tonnes=100.0, actor_supply_tonnes=0.0,
                founder_sales_tonnes=0.0, stock_tonnes=0.0)
    base.update(changes)
    return market.MarketConditions(**base)


TERMS = trader_response.TraderTerms(cost_share_of_price=0.10, adjustment_share=0.25)


def trade(foreign_price, terms=TERMS, previous=0.0, freight=2.0, **limits):
    home = conditions(society_capacity_tonnes=70.0)
    return trader_response.clear_with_traders(
        home, conditions(), 100.0, foreign_price, freight, terms, previous, **limits)


class CostTests(unittest.TestCase):
    def test_cost_share_adds_margin_loss_and_interest_over_the_cycle(self):
        share = trader_response.cost_share_of_price(
            margin_share=0.02, loss_share=0.01, market_rate=0.10, cycle_years=0.5)
        self.assertAlmostEqual(share, 0.02 + 0.01 / 0.99 + 0.05)

    def test_a_longer_cycle_or_a_higher_rate_costs_more(self):
        base = trader_response.cost_share_of_price(0.02, 0.0, 0.10, 0.5)
        self.assertGreater(trader_response.cost_share_of_price(0.02, 0.0, 0.10, 1.0), base)
        self.assertGreater(trader_response.cost_share_of_price(0.02, 0.0, 0.20, 0.5), base)


class ResponseTests(unittest.TestCase):
    def test_a_few_percent_gap_after_freight_moves_nothing(self):
        # Balanced markets, long-run prices 3 per cent apart, freight 2: the plain rule ships.
        plain = trade_between.clear_trading_markets(
            conditions(), conditions(), 100.0, 97.0, 2.0)
        self.assertGreater(plain.flow_tonnes, 0.0)
        merchants = trader_response.clear_with_traders(
            conditions(), conditions(), 100.0, 97.0, 2.0, TERMS, 0.0)
        self.assertEqual(merchants.flow_tonnes, 0.0)

    def test_a_larger_gap_moves_more(self):
        small = trade(foreign_price=88.0).flow_tonnes
        large = trade(foreign_price=60.0).flow_tonnes
        self.assertGreater(small, 0.0)
        self.assertGreater(large, small)

    def test_one_year_closes_only_the_adjustment_share_of_the_arbitrage_volume(self):
        full = trader_response.clear_with_traders(
            conditions(society_capacity_tonnes=70.0), conditions(), 100.0, 60.0, 2.0,
            trader_response.TraderTerms(0.10, 1.0), 0.0).flow_tonnes
        first = trade(foreign_price=60.0).flow_tonnes
        self.assertAlmostEqual(first, 0.25 * full, delta=1e-6)

    def test_flow_builds_while_the_gap_persists_and_stays_below_the_partner_capacity(self):
        flow = 0.0
        flows = []
        for _year in range(40):
            flow = trade(foreign_price=60.0, previous=flow).flow_tonnes
            flows.append(flow)
        self.assertTrue(all(later >= earlier - 1e-9 for earlier, later in zip(flows, flows[1:])))
        self.assertLess(flows[0], flows[-1])
        self.assertLess(flows[-1], 100.0)

    def test_flow_fades_when_the_gap_closes(self):
        self.assertLess(trade(foreign_price=99.0, previous=20.0).flow_tonnes, 20.0)

    def test_fleet_lift_and_merchant_capital_limit_the_flow(self):
        free = trade(foreign_price=60.0, terms=trader_response.TraderTerms(0.10, 1.0)).flow_tonnes
        lifted = trade(foreign_price=60.0, terms=trader_response.TraderTerms(0.10, 1.0),
                       lift_into_home_tonnes=free / 4.0).flow_tonnes
        financed = trade(foreign_price=60.0, terms=trader_response.TraderTerms(0.10, 1.0, free / 5.0)
                         ).flow_tonnes
        self.assertAlmostEqual(lifted, free / 4.0, delta=1e-6)
        self.assertAlmostEqual(financed, free / 5.0, delta=1e-6)

    def test_free_trade_with_full_adjustment_is_the_plain_rule(self):
        terms = trader_response.TraderTerms(0.0, 1.0)
        plain = trade_between.clear_trading_markets(
            conditions(society_capacity_tonnes=70.0), conditions(), 100.0, 60.0, 2.0)
        mine = trade(foreign_price=60.0, terms=terms)
        self.assertAlmostEqual(mine.flow_tonnes, plain.flow_tonnes, delta=1e-6)
        self.assertTrue(math.isfinite(mine.home.price_ratio))


if __name__ == "__main__":
    unittest.main()
