"""Porters and carters have the headcount the labour core holds; a trade the core holds nobody of takes the declared floor
(Complaint 556, 964). The rule is called on a stub labour."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.labour.labour_population import PopulationMixin
from sim.labour.workforce_spinup import FARM_TRADE
from sim.constants import REGISTRY

WORKING = 60000.0
TOTAL = 100000.0
URBAN_FRACTION = 0.2
LABOUR_FAMILY = ("porter", "carter", "sailor", "miner")


class _Labour(PopulationMixin):
    def __init__(self, core):
        self._core = core
        families = {trade: "labour" for trade in LABOUR_FAMILY + (FARM_TRADE, "labourer")}
        families["smith"] = "craft"
        household = types.SimpleNamespace(trades_created=set(), trade_schools={})
        self._world = types.SimpleNamespace(
            wages={trade: 1.0 for trade in families}, trades_absent=set(), trade_family=lambda trade: families[trade],
            civ={"urban_fraction": URBAN_FRACTION}, urban_fraction=lambda: URBAN_FRACTION, trade_registry={"labourer": {"fallback": True}},
            workforce=household, view=workforce_stand_in.view_of(household), state=types.SimpleNamespace(household=household, economy=types.SimpleNamespace()), society=types.SimpleNamespace(society_labour_hours={}),
            population=types.SimpleNamespace(working_age=WORKING, total=TOTAL))

    def core_people_by_trade(self):
        return self._core


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
