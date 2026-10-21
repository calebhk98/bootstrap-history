"""A trade's people come from its share of work, not from a hand-written class (Complaint 640: the rules are called
on a stub labour built here; the hiring cap and the national count on a whole game are in
test_labour_population_derived_scenario)."""
QUICK_TOPIC = True

import ast
import types
import unittest

from sim.labour.workforce_spinup import FARM_TRADE

from .harness import *  # noqa: F401,F403
from sim.labour import labour_population
from sim.labour.labour_population import PopulationMixin

WORKING_PEOPLE = 60000.0
FAMILIES = {FARM_TRADE: "farm", "hand": "farm", "smith": "craft", "potter": "craft", "scholar": "scholar", "moddedtrade": "craft"}


class _StubLabour(PopulationMixin):
    """Only what a trade's people read: its share of work, the town's working people and the trade registry."""

    def __init__(self, need_shares=None, hours=None, absent=(), literate=(), farm_family_trades=()):
        self._shares = dict(need_shares or {})
        families = dict(FAMILIES, **{trade: "farm" for trade in farm_family_trades})
        household = types.SimpleNamespace(trades_created=set(), trade_schools={})
        self._world = types.SimpleNamespace(
            wages={trade: 1.0 for trade in families}, trades_absent=set(absent), trade_family=lambda trade: families.get(trade, "craft"),
            state=types.SimpleNamespace(household=household, economy=types.SimpleNamespace(society_labour_hours=dict(hours or {}))),
            trade_registry={trade: {"literate": True} for trade in literate},
            population=types.SimpleNamespace(working_age=WORKING_PEOPLE, total=2.0 * WORKING_PEOPLE))

    def _non_farm_need_shares(self):
        return self._shares

    def reach_population_estimate(self):
        return 2.0 * WORKING_PEOPLE


class DerivedPopulationTests(unittest.TestCase):

    def test_unknown_trade_gets_people_from_its_share_without_code(self):
        labour = _StubLabour({"moddedtrade": 0.1})
        self.assertAlmostEqual(labour._town_people_of_trade("moddedtrade"), WORKING_PEOPLE * 0.1)
        self.assertIsNone(labour._trade_density_source("moddedtrade"))

    def test_trade_with_no_demand_gets_declared_floor(self):
        labour = _StubLabour({})
        self.assertAlmostEqual(labour._town_people_of_trade("moddedtrade"), WORKING_PEOPLE * labour.NO_DEMAND_TRADE_SHARE)
        self.assertEqual(labour._trade_density_source("moddedtrade"), "NO_DEMAND_TRADE_SHARE")

    def test_a_share_below_the_floor_is_lifted_to_the_floor(self):
        labour = _StubLabour({"moddedtrade": labour_floor() / 10.0})
        self.assertAlmostEqual(labour._town_people_of_trade("moddedtrade"), WORKING_PEOPLE * labour.NO_DEMAND_TRADE_SHARE)

    def test_a_trade_in_the_farm_trades_family_draws_on_the_unskilled_pool(self):
        labour = _StubLabour({}, farm_family_trades=("moddedhand",))
        self.assertEqual(labour._trade_density_source("moddedhand"), "UNSKILLED_POOL_TOWN_SHARE")
        self.assertAlmostEqual(labour._town_people_of_trade("moddedhand"), WORKING_PEOPLE * labour.UNSKILLED_POOL_TOWN_SHARE)
        self.assertGreater(labour._town_people_of_trade("moddedhand"), labour._town_people_of_trade("moddedtrade"))

    def test_more_need_means_more_people_in_proportion(self):
        small = _StubLabour({"moddedtrade": 0.05})._town_people_of_trade("moddedtrade")
        large = _StubLabour({"moddedtrade": 0.10})._town_people_of_trade("moddedtrade")
        self.assertAlmostEqual(large / small, 2.0)

    def test_live_society_hours_override_need(self):
        labour = _StubLabour({"moddedtrade": 0.05}, hours={"moddedtrade": 30.0, "othertrade": 70.0, FARM_TRADE: 900.0})
        self.assertAlmostEqual(labour._share_of_town_work("moddedtrade"), 0.3)

    def test_the_farm_trade_is_not_counted_in_the_share_of_non_farm_work(self):
        labour = _StubLabour({}, hours={"smith": 25.0, "potter": 75.0, FARM_TRADE: 10000.0})
        self.assertAlmostEqual(labour._share_of_town_work("smith"), 0.25)

    def test_with_neither_hours_nor_need_the_share_is_zero(self):
        self.assertEqual(_StubLabour({})._share_of_town_work("moddedtrade"), 0.0)

    def test_a_trade_with_a_share_is_demand_derived_and_a_lettered_one_is_not(self):
        labour = _StubLabour({"smith": 0.1, "scholar": 0.1}, literate=("scholar",))
        self.assertTrue(labour._is_demand_derived("smith"))
        self.assertFalse(labour._is_demand_derived("scholar"))
        self.assertEqual(labour._trade_density_source("scholar"), "SCHOLAR_ENGAGEMENT_FRACTION")

    def test_an_absent_trade_has_no_density_source(self):
        self.assertIsNone(_StubLabour({}, absent=("moddedtrade",))._trade_density_source("moddedtrade"))

    def test_no_trade_id_literal_in_module(self):
        with open(labour_population.__file__, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        trade_ids = set(WAGES)
        self.assertTrue(trade_ids)
        docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                      if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
                      and node.body and isinstance(node.body[0], ast.Expr)
                      and isinstance(node.body[0].value, ast.Constant)}
        found = [node.value for node in ast.walk(tree)
                 if isinstance(node, ast.Constant) and isinstance(node.value, str)
                 and id(node) not in docstrings and node.value in trade_ids]
        self.assertEqual(found, [])


def labour_floor():
    return PopulationMixin.NO_DEMAND_TRADE_SHARE


if __name__ == "__main__":
    unittest.main()
