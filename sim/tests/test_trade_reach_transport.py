"""The people of a trade the household reaches are the towns within a hire's travel budget, over the
routes the technologies held open (geography's reach)."""
import unittest

from .harness import *  # noqa: F401,F403


class TradeReachTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labour = sim().labour

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
        self.labour.HIRE_TRAVEL_DAYS = 60.0
        try:
            self.assertGreater(self.labour._town_people_of_trade("smith"), base)
        finally:
            del self.labour.HIRE_TRAVEL_DAYS


if __name__ == "__main__":
    unittest.main()
