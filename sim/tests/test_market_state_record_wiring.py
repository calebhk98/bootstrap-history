"""Complaint 508 / 507 stage 6: what `market_state` reports as a market's sales, unsold stock and unmet demand is the
agent economy's record of that market, not the engine's static commodity book; a tithe falls on the sold tonnes at the
quote. Each test calls one method on a stand-in carrying only what it reads."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import market_stand_in

from sim.actors.world_stakes import StakeView
from sim.tests.world_stand_in import fake_needs


def stand_in(record, founder_sold=0.0):
    return market_stand_in.markets_over(
        economy=types.SimpleNamespace(agent_market_record=lambda commodity: record),
        goods_market=types.SimpleNamespace(sold_tonnes=lambda commodity, party: founder_sold, acting_party_id="founder"),
        material_pool=lambda material: (material, None))


class MarketState(unittest.TestCase):
    def test_sales_unsold_and_unmet_are_the_economys_record(self):
        state = stand_in({"sold": 1.0, "unsold": 2.0, "unmet": 3.0}).market_state("iron")
        self.assertEqual((state["society_sales_tonnes"], state["unsold_tonnes"], state["unmet_demand_tonnes"]), (1.0, 2.0, 3.0))

    def test_what_the_founder_sold_is_displaced_from_the_societys_sales_up_to_what_the_market_sold(self):
        state = stand_in({"sold": 5.0, "unsold": 0.0, "unmet": 0.0}, founder_sold=2.0).market_state("iron")
        self.assertEqual((state["displaced_by_founder_tonnes"], state["society_sales_tonnes"]), (2.0, 3.0))
        state = stand_in({"sold": 5.0, "unsold": 0.0, "unmet": 0.0}, founder_sold=9.0).market_state("iron")
        self.assertEqual((state["displaced_by_founder_tonnes"], state["society_sales_tonnes"]), (5.0, 0.0))

    def test_a_commodity_the_economy_has_no_record_of_has_no_state(self):
        self.assertIsNone(stand_in(None).market_state("iron"))


class TithableSales(unittest.TestCase):
    def value(self, quotes, states):
        needs = fake_needs(material_commodity=lambda material: material, market_state=lambda commodity: states.get(commodity),
                           materials_serving=lambda need: ["wheat", "rice", "ghost"])
        view = types.SimpleNamespace(needs=needs, _commodity_quote=lambda commodity: quotes.get(commodity))
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
