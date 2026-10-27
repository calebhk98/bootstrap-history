"""Porters and carters have the headcount their work gives: where the labour core holds nobody of a labour-family trade,
the national estimate is the trade's share of the society's work over the urban working people, so two trades of one
family differ by their work (Complaint 556). Only the fallback trade, the unskilled pool, keeps a town share (a labelled
heuristic, UNSKILLED_POOL_TOWN_SHARE). The rule is called on a stub labour."""
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
SHARES = {"porter": 0.30, "carter": 0.02, "smith": 0.10}      # the need differs a great deal between the two carriers


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

    def _non_farm_need_shares(self):
        return SHARES


def _urban_working():
    return TOTAL * URBAN_FRACTION * (WORKING / TOTAL)


class FamilyHeadcountFollowsWorkTests(unittest.TestCase):

    def test_with_no_core_people_a_labour_family_trade_has_its_share_of_work(self):
        labour = _Labour({})
        self.assertAlmostEqual(labour.national_trade_population("porter"), _urban_working() * SHARES["porter"])
        self.assertAlmostEqual(labour.national_trade_population("carter"), _urban_working() * SHARES["carter"])

    def test_porters_and_carters_differ_by_their_work(self):
        labour = _Labour({})
        self.assertNotEqual(labour.national_trade_population("porter"), labour.national_trade_population("carter"))
        ratio = labour.national_trade_population("porter") / labour.national_trade_population("carter")
        self.assertAlmostEqual(ratio, SHARES["porter"] / SHARES["carter"])

    def test_a_family_trade_with_no_work_gets_the_floor_not_a_town_share(self):
        labour = _Labour({})
        self.assertAlmostEqual(labour.national_trade_population("sailor"), _urban_working() * labour.NO_DEMAND_TRADE_SHARE)

    def test_the_unskilled_pool_keeps_its_town_share(self):
        labour = _Labour({})
        self.assertAlmostEqual(labour.national_trade_population("labourer"), _urban_working() * labour.UNSKILLED_POOL_TOWN_SHARE)

    def test_where_the_core_holds_people_their_count_is_used_and_the_two_trades_differ(self):
        labour = _Labour({"porter": 120.0, "carter": 30.0})
        self.assertEqual(labour.national_trade_population("porter"), 120.0)
        self.assertEqual(labour.national_trade_population("carter"), 30.0)

    def test_the_shares_are_labelled_temporary_heuristics_that_name_556(self):
        for name in ("UNSKILLED_POOL_TOWN_SHARE", "NO_DEMAND_TRADE_SHARE"):
            self.assertEqual(REGISTRY[name]["kind"], "temporary_heuristic")
            self.assertIn("556", REGISTRY[name]["retire"])


if __name__ == "__main__":
    unittest.main()
