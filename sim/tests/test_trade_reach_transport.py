"""The people of a trade the household reaches depend on how far travel takes them."""
import unittest

from .harness import *  # noqa: F401,F403


class TradeReachTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labour = sim().labour

    def test_walking_pace_reaches_only_the_home_town(self):
        self.assertAlmostEqual(self.labour.reach_population_estimate(),
                               self.labour.home_town_population_estimate())

    def test_faster_travel_reaches_more_people(self):
        walking = self.labour.reach_population_estimate(self.labour.travel_speed_km_per_day())
        faster = self.labour.reach_population_estimate(self.labour.travel_speed_km_per_day() * 20)
        self.assertGreater(faster, walking)

    def test_reach_never_shrinks_with_speed(self):
        speeds = [0.0, 10.0, 50.0, 200.0, 2000.0]
        reach = [self.labour.reach_population_estimate(speed) for speed in speeds]
        self.assertEqual(reach, sorted(reach))
        self.assertAlmostEqual(reach[0], self.labour.home_town_population_estimate())

    def test_trade_people_follow_the_reach(self):
        base = self.labour._town_people_of_trade("smith")
        self.labour.travel_speed_km_per_day = lambda: 5000.0
        try:
            self.assertGreater(self.labour._town_people_of_trade("smith"), base)
        finally:
            del self.labour.travel_speed_km_per_day


if __name__ == "__main__":
    unittest.main()
