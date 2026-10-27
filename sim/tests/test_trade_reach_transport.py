"""The people of a trade the household reaches are the towns within a hire's travel budget, over the
routes the technologies held open (geography's reach). Complaint 640: the reach is read off the labour mixins over a
stand-in world that holds the nation's tiles, people and trade hours, so no game is built."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.data import load_civ
from sim.geography.api import tiles_held
from sim.labour.labour_capacity import CapacityMixin
from sim.labour.labour_population import PopulationMixin
from sim.labour.labour_settlement import SettlementMixin
from sim.tests import harness  # noqa: F401  (isolates the home directory)

NATION = 20.0e6
HOURS_BY_TRADE = {"smith": 3000.0, "mason": 2000.0, "farmer": 90000.0}


class ReachLabour(SettlementMixin, PopulationMixin):
    """The labour mixins that size a town and the people of a trade within reach of it, over a stand-in world."""

    POP_SCALE_FLOOR_SHARE = CapacityMixin.POP_SCALE_FLOOR_SHARE
    POP_SCALE_VARIABLE_SHARE = CapacityMixin.POP_SCALE_VARIABLE_SHARE

    def __init__(self):
        homes = tuple(tiles_held(load_civ("rome_100ad")))
        economy = types.SimpleNamespace(improvements={}, society_labour_hours=dict(HOURS_BY_TRADE))
        self._world = types.SimpleNamespace(
            home_tiles_held=lambda: homes, population=types.SimpleNamespace(total=NATION, working_age=0.55 * NATION), pop_scale=1.0,
            provided_town_population=lambda labour, tile, nominal_people: None, has_town_premiums=lambda: False,
            people_by_tile=lambda: None, held_and_running=lambda: (), built_ways=lambda: {}, wages=dict.fromkeys(HOURS_BY_TRADE, 1.0),
            trade_family=lambda trade: "farm" if trade == "farmer" else "craft",
            workforce=types.SimpleNamespace(trade_schools={}, trades_created=set(), employees={}),
            society=types.SimpleNamespace(society_labour_hours=dict(HOURS_BY_TRADE)),
            state=types.SimpleNamespace(household=types.SimpleNamespace(base_tile=None), economy=economy))


class TradeReachTransportTests(unittest.TestCase):
    def setUp(self):
        self.labour = ReachLabour()

    def test_a_days_travel_reaches_only_the_home_town(self):
        self.assertAlmostEqual(self.labour.reach_population_estimate(),
                               self.labour.home_town_population_estimate())

    def test_a_longer_budget_reaches_more_people(self):
        self.assertGreater(self.labour.reach_population_estimate(30.0), self.labour.reach_population_estimate(1.0))

    def test_reach_never_shrinks_with_the_budget(self):
        budgets = [0.0, 1.0, 3.0, 10.0, 60.0]
        reach = [self.labour.reach_population_estimate(days) for days in budgets]
        self.assertEqual(reach, sorted(reach))
        self.assertAlmostEqual(reach[0], self.labour.home_town_population_estimate())

    def test_reach_comes_from_geography_over_the_modes_held(self):
        tiles = self.labour.reachable_tiles(30.0)
        self.assertIn(self.labour.base_tile(), tiles)
        self.assertTrue(all(days <= 30.0 for days in tiles.values()))

    def test_trade_people_follow_the_reach(self):
        base = self.labour._town_people_of_trade("smith")
        self.assertGreater(base, 0.0)
        self.labour.HIRE_TRAVEL_DAYS = 60.0
        self.assertGreater(self.labour._town_people_of_trade("smith"), base)

    def test_a_trade_with_more_of_the_towns_work_has_more_people(self):
        self.assertGreater(self.labour._town_people_of_trade("smith"), self.labour._town_people_of_trade("mason"))


if __name__ == "__main__":
    unittest.main()
