"""Complaint 508 / 507 stage 6: what `market_state` reports as a market's sales, unsold stock and unmet demand is the
agent economy's record of that market, not the engine's static commodity book; a tithe falls on the sold tonnes at the
quote. Each test calls one method on a stand-in carrying only what it reads."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import agents_port_stakes, market_clearing
from sim.engine.agents_port_stakes import StakeView
from sim.engine.market_clearing import MarketClearingMixin

CLOSING = types.SimpleNamespace(price_ratio=1.1, society_sales_tonnes=7.0, unsold_tonnes=8.0, unmet_demand_tonnes=9.0)


def stand_in(record):
    conditions = types.SimpleNamespace(
        floor_ratio=0.5, ceiling_ratio=2.0, household_demand_at_anchor_tonnes=3.0, actor_supply_tonnes=1.0,
        actor_demand_tonnes=2.0, founder_sales_tonnes=0.0)
    outcome = types.SimpleNamespace(price_ratio=1.0)
    return types.SimpleNamespace(
        _material_tag=lambda material: (material, None),
        _market_outcome=lambda commodity, with_flows=False: (
            (conditions, CLOSING) if with_flows else (conditions, outcome)),
        _market_entry=lambda commodity: {"capacity_tonnes": 1.0, "reference_tonnes": 2.0, "stock_tonnes": 3.0},
        economy=types.SimpleNamespace(agent_market_record=lambda commodity: record),
        goods_market=types.SimpleNamespace(
            bought_tonnes=lambda commodity, party: 0.0, drawn_tonnes=lambda commodity: 0.0,
            acting_party_id="founder", others_offers=lambda commodity: []))


class MarketState(unittest.TestCase):
    def state(self, record):
        with mock.patch.object(market_clearing.market, "society_sales_displaced_by_founder", lambda conditions: 0.0):
            return MarketClearingMixin.market_state(stand_in(record), "iron")

    def test_sales_unsold_and_unmet_are_the_economys_record_when_it_has_one(self):
        state = self.state({"sold": 1.0, "unsold": 2.0, "unmet": 3.0})
        self.assertEqual((state["society_sales_tonnes"], state["unsold_tonnes"], state["unmet_demand_tonnes"]),
                         (1.0, 2.0, 3.0))

    def test_they_are_the_static_books_only_while_the_economy_has_no_record(self):
        state = self.state(None)
        self.assertEqual((state["society_sales_tonnes"], state["unsold_tonnes"], state["unmet_demand_tonnes"]),
                         (7.0, 8.0, 9.0))

    def test_a_commodity_with_no_market_has_no_state(self):
        view = stand_in(None)
        view._market_outcome = lambda commodity, with_flows=False: None
        self.assertIsNone(MarketClearingMixin.market_state(view, "iron"))


class TithableSales(unittest.TestCase):
    def value(self, quotes, states):
        sim = types.SimpleNamespace(
            economy=types.SimpleNamespace(commodity_of=lambda material: material),
            market_state=lambda commodity: states.get(commodity))
        view = types.SimpleNamespace(_sim=sim, _commodity_quote=lambda commodity: quotes.get(commodity))
        with mock.patch.object(agents_port_stakes.need_substitutes, "serving", lambda need: ["wheat", "rice", "ghost"]):
            return StakeView.tithable_sales_value(view, "food")

    def test_the_value_is_the_sold_tonnes_at_the_buy_quote_summed_over_the_needs_commodities(self):
        quotes = {"wheat": {"buy_per_tonne": 10.0}, "rice": {"buy_per_tonne": 20.0}}
        states = {"wheat": {"society_sales_tonnes": 3.0}, "rice": {"society_sales_tonnes": 2.0}}
        self.assertAlmostEqual(self.value(quotes, states), 3.0 * 10.0 + 2.0 * 20.0)

    def test_a_commodity_without_a_quote_or_a_market_adds_nothing(self):
        quotes = {"wheat": {"buy_per_tonne": 10.0}}
        states = {"wheat": {"society_sales_tonnes": 3.0}, "rice": {"society_sales_tonnes": 99.0}}
        self.assertAlmostEqual(self.value(quotes, states), 30.0)


if __name__ == "__main__":
    unittest.main()
