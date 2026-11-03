"""A trade's people are the labour core's, with one declared floor where the core holds nobody of it (Complaint 640, 964: the
rules are called on a stub labour built here; the hiring cap and the national count on a whole game are in
test_labour_population_derived_scenario)."""
QUICK_TOPIC = True

import types
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour.labour_population_report import PopulationReport
from sim.labour.labour_supply import Supply
from sim.labour.labour_trades import Trades

WORKING_PEOPLE = 60000.0
FAMILIES = {"smith": "craft", "scholar": "scholar", "moddedtrade": "craft"}


class _StubLabour:
    """Only what a trade's people read: the core's people by tile, the tiles reached and the trade registry."""

    def __init__(self, core_by_tile=None, absent=(), literate=()):
        self._core_by_tile = core_by_tile
        household = types.SimpleNamespace(trades_created=set(), trade_schools={})
        self._world = types.SimpleNamespace(
            trades=types.SimpleNamespace(
                wages={trade: 1.0 for trade in FAMILIES}, HOURS_PER_PERSON_YEAR=2000.0, trades_absent=set(absent),
                trade_family=lambda trade: FAMILIES.get(trade, "craft"),
                trade_registry={trade: {"literate": True} for trade in literate}),
            workforce=household,
            economy=types.SimpleNamespace(
                agent_working_hours=lambda: None,
                agent_hours_offered_at=lambda trade, tile: None if core_by_tile is None else core_by_tile.get(tile, {}).get(trade, 0.0) * 2000.0),
            people=types.SimpleNamespace(population=types.SimpleNamespace(working_age=WORKING_PEOPLE, total=2.0 * WORKING_PEOPLE)))
        self.NO_DEMAND_TRADE_SHARE = Supply.NO_DEMAND_TRADE_SHARE
        trades = Trades(self._world)
        self.supply = Supply(self._world, book=self, capacity=None, settlement=self, trades=trades)
        self.report = PopulationReport(self._world, book=self, settlement=self, supply=self.supply, trades=trades)

    def _people_of_trade_in_reach(self, trade):
        return self.supply._people_of_trade_in_reach(trade)

    def _trade_density_source(self, trade):
        return self.report._trade_density_source(trade)

    def core_people_by_trade(self):
        if self._core_by_tile is None:
            return None
        totals = {}
        for by_trade in self._core_by_tile.values():
            for trade, people in by_trade.items():
                totals[trade] = totals.get(trade, 0.0) + people
        return totals

    def reachable_tiles(self, days_budget=None):
        return {"near": 0.5}

    def base_tile(self):
        return "home"

    def reach_population_estimate(self):
        return 2.0 * WORKING_PEOPLE


class PeopleInReachTests(unittest.TestCase):

    def test_the_people_the_base_tiles_households_offer_are_the_trades_people(self):
        labour = _StubLabour({"home": {"moddedtrade": 30.0}, "near": {"moddedtrade": 12.0}, "far": {"moddedtrade": 500.0}})
        self.assertEqual(labour._people_of_trade_in_reach("moddedtrade"), 30.0)
        self.assertIsNone(labour._trade_density_source("moddedtrade"))

    def test_a_trade_the_core_holds_nobody_of_gets_the_declared_floor(self):
        labour = _StubLabour({"home": {"smith": 30.0}})
        self.assertAlmostEqual(labour._people_of_trade_in_reach("moddedtrade"), 2.0 * WORKING_PEOPLE * 0.5 * labour.NO_DEMAND_TRADE_SHARE)
        self.assertEqual(labour._trade_density_source("moddedtrade"), "NO_DEMAND_TRADE_SHARE")

    def test_before_the_core_opens_the_trade_takes_the_declared_floor(self):
        labour = _StubLabour(None)
        self.assertGreater(labour._people_of_trade_in_reach("smith"), 0.0)
        self.assertEqual(labour._trade_density_source("smith"), "NO_DEMAND_TRADE_SHARE")

    def test_a_lettered_trade_and_an_absent_one_have_no_density_source(self):
        self.assertIsNone(_StubLabour({}, literate=("scholar",))._trade_density_source("scholar"))
        self.assertIsNone(_StubLabour({}, absent=("moddedtrade",))._trade_density_source("moddedtrade"))


if __name__ == "__main__":
    unittest.main()
