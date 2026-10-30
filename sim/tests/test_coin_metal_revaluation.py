"""Complaint 135: the coin's value follows its metal's market price (a glut inflates, a shortage deflates),
stock sells below the producers' floor on its own bound, wages read the clearing, and the partners' books use
the running-share floor."""

QUICK_TOPIC = True

import types
import unittest

from sim.coin.module import Coin
from sim.coin.state import CoinWorld
from sim.foreign_trade.module import ForeignTrade
from sim.labour.labour_wages import WagesMixin
from sim.reporting.api import ReportingWorld
from sim.reporting.module import Reporting
from sim.tests import module_harness
from sim.tests.test_capital_charge import works_entry
from sim.tests.test_running_cost_floor import StubGame
from sim.world import market

CONDITIONS = dict(
    household_demand_at_anchor_tonnes=100.0, committed_demand_tonnes=0.0, society_capacity_tonnes=100.0,
    actor_supply_tonnes=0.0, founder_sales_tonnes=0.0, stock_tonnes=0.0, floor_ratio=0.6, ceiling_ratio=6.0)


def coinage(measured=None):
    """The coin module over a home silver standard and one partner on gold; `measured` is the market's ratio by metal."""
    measured = measured or {}
    return module_harness.build(Coin, world=CoinWorld(), views={
        "civilisation": {"coin_standard": {"material": "silver_kg"}}, "opening_population": 1000.0,
        "opening_money_per_labour_hour": 0.5, "foreign_coin_home_units": 0.0, "foreign_economies": ["x"],
        "foreign_coin_partner_units": {"x": 0.0}, "partner_coin_standard": {"x": {"material": "gold_kg"}},
        "partner_opening_facts": {"x": {"population": 1000.0, "money_per_labour_hour": 0.5}},
        "coin_value_ratio": lambda metal: measured.get(metal, 1.0)})


class RevaluationTests(unittest.TestCase):
    def test_a_glut_of_the_coin_metal_raises_the_price_level(self):
        game = coinage()
        before = game.home_price_level()
        game.world.metal_ratios["silver_kg"] = 0.5
        self.assertAlmostEqual(game.home_price_level(), before * 2.0)

    def test_a_shortage_lowers_it(self):
        game = coinage()
        game.world.metal_ratios["silver_kg"] = 2.0
        self.assertAlmostEqual(game.home_price_level(), 0.5)

    def test_another_metal_leaves_the_level_alone(self):
        game = coinage()
        game.world.metal_ratios["gold_kg"] = 0.5
        self.assertAlmostEqual(game.home_price_level(), 1.0)

    def test_a_partners_price_level_follows_its_coin_metal(self):
        game = coinage()
        flat = game.partner_price_level("x")
        game.world.metal_ratios["gold_kg"] = 0.25
        self.assertAlmostEqual(game.partner_price_level("x"), flat * 4.0)

    def test_revaluing_stores_the_market_ratio_of_each_coin_metal(self):
        game = coinage({"silver_kg": 0.8, "gold_kg": 1.5})
        for _year in range(60):
            game.revalue_coin_metals(["seat"])    # damped: it closes on the measured value over the years
        ratios = game.world.metal_ratios
        self.assertAlmostEqual(ratios["silver_kg"], 0.8, places=4)
        self.assertAlmostEqual(ratios["gold_kg"], 1.5, places=4)


class StockBoundTests(unittest.TestCase):
    def test_producers_idle_at_their_floor_when_nothing_else_is_on_offer(self):
        conditions = market.MarketConditions(**dict(CONDITIONS, household_demand_at_anchor_tonnes=10.0))
        self.assertAlmostEqual(market.clear_market(conditions).price_ratio, 0.6, places=3)

    def test_stock_sells_below_the_producers_floor(self):
        conditions = market.MarketConditions(**dict(CONDITIONS, stock_tonnes=500.0))
        outcome = market.clear_market(conditions)
        self.assertLess(outcome.price_ratio, 0.6)
        self.assertEqual(outcome.society_sales_tonnes, 0.0)

    def test_the_stock_bound_is_its_own(self):
        conditions = market.MarketConditions(**dict(CONDITIONS, stock_tonnes=1e9, stock_floor_ratio=0.2))
        self.assertAlmostEqual(market.clear_market(conditions).price_ratio, 0.2, places=3)


class PartnerFloorTests(unittest.TestCase):
    def test_a_partners_book_uses_the_running_share_floor(self):
        game = StubGame(works_entry())
        partner_books = module_harness.build(ForeignTrade, views={
            "market_floor_ratio": game._floor_ratio,
            "commodity_record": {"widget": {"price_floor_factor": 0.99, "price_ceiling_factor": 3.0}}})
        entry = {"reference_tonnes": 10.0, "capacity_tonnes": 100.0, "stock_tonnes": 0.0}
        outcome = partner_books._partner_outcome(entry, "widget", 0.0, 0.0)
        self.assertAlmostEqual(outcome.price_ratio, game.commodity_floor_ratio("widget"), places=3)
        self.assertLess(outcome.price_ratio, 0.99)


class WageStub(WagesMixin):
    WAGE_SHARE_FOOD, WAGE_SHARE_HOUSING, WAGE_SHARE_TOOLS, WAGE_SHARE_SKILL_AND_DIFFICULTY = 0.5, 0.0, 0.5, 0.0

    def __init__(self, ratios):
        self._world = types.SimpleNamespace(
            civ={"staple": "wheat_kg"}, trade_registry={"smith": {"tool_basket": ["iron_kg"]}},
            last_market_price_ratio=lambda material: ratios.get(material, 1.0),
            material_price_factor=lambda material: 1.0)

    @property
    def labour_market(self):
        return types.SimpleNamespace(town_housing_factor=lambda: 1.0)


class WageClearingTests(unittest.TestCase):
    def test_the_food_and_tool_terms_read_the_clearing(self):
        flat = WageStub({}).wage_cost_factors("smith")
        dear = WageStub({"wheat_kg": 2.0, "iron_kg": 3.0}).wage_cost_factors("smith")
        self.assertAlmostEqual(flat["food"], 1.0)
        self.assertAlmostEqual(dear["food"], 2.0)
        self.assertAlmostEqual(dear["tools"], 3.0)


class RecordingStub:
    """The market computes a landed price, which asks for a wage: the wage must not ask the market back."""
    def __init__(self):
        self.civ = {"staple": "wheat_kg"}
        self.trade_registry = {"smith": {"tool_basket": ["iron_kg"]}}
        self.live_calls = 0
        self.reporting = module_harness.build(Reporting, world=ReportingWorld(),
                                              views={"wage_materials": ["iron_kg", "wheat_kg"]})
        self.reporting.real_price_ratio = self.market_price_ratio
        self.wages = WageStub({})
        self.wages._world = types.SimpleNamespace(
            civ=self.civ, trade_registry=self.trade_registry,
            last_market_price_ratio=self.reporting.last_market_price_ratio, material_price_factor=lambda material: 1.0)

    def record_wage_market_ratios(self):
        self.reporting.record_wage_market_ratios()

    def market_price_ratio(self, material):
        self.live_calls += 1
        self.wages.wage_cost_factors("smith")    # a landed price quotes a wage
        return 2.0


class WageRecursionTests(unittest.TestCase):
    def test_a_wage_quote_never_calls_the_live_clearing(self):
        game = RecordingStub()
        game.record_wage_market_ratios()
        self.assertEqual(game.live_calls, 2)   # the staple and the tool, once each, at the close
        calls = game.live_calls
        factors = game.wages.wage_cost_factors("smith")
        self.assertEqual(game.live_calls, calls)
        self.assertAlmostEqual(factors["food"], 2.0)
        self.assertAlmostEqual(factors["tools"], 2.0)


if __name__ == "__main__":
    unittest.main()
