"""Complaint 135: a mine's output is supply in the year's clearing. The site cap on a mine's runs is
test_economy_sites; whether a mine's ore moves the price over years is measured by `python3 sim/simulator.py economy-check`.
Engine path: the society's baseline capacity is the deposits' output (their quantities are shares of
the empire output table, scaled by the reach to the tiles held, geography.mineral_scale), and any mine a
concern runs is an offer at its own cost (producer_costs.founder_concern_offers, goods_market.others_offers)."""

QUICK_TOPIC = True

import unittest
from sim.world import market
from sim.world.producer_market import Offer


class EnginePathMineTests(unittest.TestCase):
    CONDITIONS = dict(household_demand_at_anchor_tonnes=100.0, committed_demand_tonnes=0.0,
                      society_capacity_tonnes=100.0, actor_supply_tonnes=0.0, founder_sales_tonnes=0.0,
                      stock_tonnes=0.0, floor_ratio=0.4)

    def test_a_concerns_mine_adds_supply_to_the_baseline_and_lowers_the_price(self):
        alone = market.clear_market(market.MarketConditions(**self.CONDITIONS))
        with_mine = market.clear_market(market.MarketConditions(**self.CONDITIONS, offers=(Offer(60.0, 0.5),)))
        self.assertLess(with_mine.price_ratio, alone.price_ratio)
        self.assertGreater(with_mine.offers_sold_tonnes, 0.0)


if __name__ == "__main__":
    unittest.main()
