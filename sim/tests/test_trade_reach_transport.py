"""The people of a trade the household reaches are the towns within a hire's travel budget, over the
routes the technologies held open (geography's reach). Complaint 640: the reach is read off the labour parts over a
stand-in world that holds the nation's tiles, people and trade hours, so no game is built."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.data import load_civ
from sim.geography.api import tiles_held
from sim.labour.labour_settlement import Settlement
from sim.labour.labour_supply import Supply
from sim.labour.staff_book import StaffBook

NATION = 20.0e6
HOURS_BY_TRADE = {"smith": 3000.0, "mason": 2000.0, "farmer": 90000.0}


class ReachLabour:
    """The labour parts that size a town and the people of a trade within reach of it, over a stand-in world."""

    def __init__(self):
        homes = tuple(tiles_held(load_civ("rome_100ad")))
        economy = types.SimpleNamespace(improvements={}, society_labour_hours=dict(HOURS_BY_TRADE))
        self._world = types.SimpleNamespace(
            home_tiles_held=lambda: homes, population=types.SimpleNamespace(total=NATION, working_age=0.55 * NATION), pop_scale=1.0,
            provided_town_population=lambda tile, nominal_people: None, has_town_premiums=lambda: False,
            people_by_tile=lambda: None, held_and_running=lambda: (), built_ways=lambda: {}, wages=dict.fromkeys(HOURS_BY_TRADE, 1.0),
            trade_family=lambda trade: "farm" if trade == "farmer" else "craft",
            workforce=types.SimpleNamespace(trade_schools={}, trades_created=set(), employees={}, base_tile=None),
            society=types.SimpleNamespace(society_labour_hours=dict(HOURS_BY_TRADE)),
            state=types.SimpleNamespace(economy=economy))
        self.settlement = Settlement(self._world)
        self.book = StaffBook(self._world)
        self.supply = Supply(self._world, book=self.book, capacity=None, settlement=self.settlement, trades=None)


class TradeReachTransportTests(unittest.TestCase):
    def setUp(self):
        self.labour = ReachLabour()

    def test_a_days_travel_reaches_only_the_home_town(self):
        self.assertAlmostEqual(self.labour.settlement.reach_population_estimate(),
                               self.labour.settlement.home_town_population_estimate())

    def test_a_longer_budget_reaches_more_people(self):
        self.assertGreater(self.labour.settlement.reach_population_estimate(30.0), self.labour.settlement.reach_population_estimate(1.0))

    def test_reach_never_shrinks_with_the_budget(self):
        budgets = [0.0, 1.0, 3.0, 10.0, 60.0]
        reach = [self.labour.settlement.reach_population_estimate(days) for days in budgets]
        self.assertEqual(reach, sorted(reach))
        self.assertAlmostEqual(reach[0], self.labour.settlement.home_town_population_estimate())

    def test_reach_comes_from_geography_over_the_modes_held(self):
        tiles = self.labour.settlement.reachable_tiles(30.0)
        self.assertIn(self.labour.settlement.base_tile(), tiles)
        self.assertTrue(all(days <= 30.0 for days in tiles.values()))

    def test_trade_people_follow_the_reach(self):
        self.labour.book.core_people_by_tile_and_trade = lambda: {tile: {"smith": 10.0} for tile in self.labour.settlement.settlement_tiles()}
        base = self.labour.supply._people_of_trade_in_reach("smith")
        self.assertEqual(base, 10.0)
        self.labour.settlement.HIRE_TRAVEL_DAYS = 60.0
        self.assertGreater(self.labour.supply._people_of_trade_in_reach("smith"), base)


if __name__ == "__main__":
    unittest.main()
