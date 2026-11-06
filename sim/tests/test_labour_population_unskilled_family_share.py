"""Porters and carters have the headcount the labour core holds; a trade the core holds nobody of takes the declared floor
(Complaint 556, 964). The rule is called on a stub labour."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_supply import Supply
from sim.labour.labour_trades import Trades
from sim.labour.trade_data import farm_trade
from sim.constants import REGISTRY

WORKING = 60000.0
TOTAL = 100000.0
URBAN_FRACTION = 0.2
LABOUR_FAMILY = ("porter", "carter", "sailor", "miner")


class _Labour:
    def __init__(self, core):
        self._core = core
        families = {trade: "labour" for trade in LABOUR_FAMILY + (farm_trade(), "labourer")}
        families["smith"] = "craft"
        household = types.SimpleNamespace(trades_created=set(), trade_schools={})
        self._world = types.SimpleNamespace(
            trades=types.SimpleNamespace(wages={trade: 1.0 for trade in families}, trades_absent=set(),
                                         trade_family=lambda trade: families[trade], trade_registry={"labourer": {"fallback": True}}),
            scenario=types.SimpleNamespace(civ={"urban_fraction": URBAN_FRACTION}),
            people=types.SimpleNamespace(urban_fraction=lambda: URBAN_FRACTION,
                                         population=types.SimpleNamespace(working_age=WORKING, total=TOTAL)),
            workforce=household)

        self.supply = Supply(self._world, book=self, capacity=None, settlement=None, trades=Trades(self._world))

    def core_people_by_trade(self):
        return self._core

    def national_trade_population(self, trade):
        return self.supply.national_trade_population(trade)


class CoreHeadcountTests(unittest.TestCase):

    def test_where_the_core_holds_people_their_count_is_used_and_the_two_trades_differ(self):
        labour = _Labour({"porter": 120.0, "carter": 30.0})
        self.assertEqual(labour.national_trade_population("porter"), 120.0)
        self.assertEqual(labour.national_trade_population("carter"), 30.0)

    def test_a_trade_the_core_holds_nobody_of_has_nobody_in_the_country(self):
        labour = _Labour({})
        self.assertEqual(labour.national_trade_population("sailor"), 0.0)

    def test_the_floor_is_a_labelled_temporary_heuristic_that_names_964(self):
        self.assertEqual(REGISTRY["NO_DEMAND_TRADE_SHARE"]["kind"], "temporary_heuristic")
        self.assertIn("964", REGISTRY["NO_DEMAND_TRADE_SHARE"]["retire"])


if __name__ == "__main__":
    unittest.main()
