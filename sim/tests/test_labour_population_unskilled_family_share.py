"""Porters and carters share one national headcount where the labour core holds nobody of either: every trade in the
farm trade's family takes the same town share of working people (a labelled heuristic, UNSKILLED_POOL_TOWN_SHARE).
The rule is called on a stub labour; the equal counts do not come from the carriage split (workforce_carriage)."""
QUICK_TOPIC = True

import types
import unittest

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
        families = {trade: "labour" for trade in LABOUR_FAMILY + (FARM_TRADE,)}
        families["smith"] = "craft"
        household = types.SimpleNamespace(trades_created=set(), trade_schools={})
        self._world = types.SimpleNamespace(
            wages={trade: 1.0 for trade in families}, trades_absent=set(), trade_family=lambda trade: families[trade],
            civ={"urban_fraction": URBAN_FRACTION}, trade_registry={},
            state=types.SimpleNamespace(household=household, economy=types.SimpleNamespace(society_labour_hours={})),
            population=types.SimpleNamespace(working_age=WORKING, total=TOTAL))

    def core_people_by_trade(self):
        return self._core

    def _non_farm_need_shares(self):
        return {"porter": 0.30, "carter": 0.02, "smith": 0.10}   # the need differs a great deal between the two carriers


class UnskilledFamilyShareTests(unittest.TestCase):
    # Pins current behaviour (a labelled heuristic, not a defect of the carriage split): the family share stands in
    # until the labour core holds the people, which Complaints/556 (one owner of labour supply) covers.

    def test_with_no_core_people_every_labour_family_trade_has_the_same_count(self):
        labour = _Labour({})
        counts = {trade: labour.national_trade_population(trade) for trade in LABOUR_FAMILY}
        self.assertEqual(len(set(counts.values())), 1)
        expected = TOTAL * URBAN_FRACTION * (WORKING / TOTAL) * labour.UNSKILLED_POOL_TOWN_SHARE
        self.assertAlmostEqual(counts["porter"], expected)

    def test_the_equal_count_ignores_how_much_work_each_trade_has(self):
        labour = _Labour({})
        self.assertNotEqual(labour._share_of_town_work("porter"), labour._share_of_town_work("carter"))
        self.assertEqual(labour.national_trade_population("porter"), labour.national_trade_population("carter"))

    def test_a_craft_trade_follows_its_share_of_work_instead(self):
        labour = _Labour({})
        self.assertNotEqual(labour.national_trade_population("smith"), labour.national_trade_population("porter"))

    def test_where_the_core_holds_people_their_count_is_used_and_the_two_trades_differ(self):
        labour = _Labour({"porter": 120.0, "carter": 30.0})
        self.assertEqual(labour.national_trade_population("porter"), 120.0)
        self.assertEqual(labour.national_trade_population("carter"), 30.0)

    def test_the_share_is_a_labelled_temporary_heuristic(self):
        self.assertEqual(REGISTRY["UNSKILLED_POOL_TOWN_SHARE"]["kind"], "temporary_heuristic")


if __name__ == "__main__":
    unittest.main()
