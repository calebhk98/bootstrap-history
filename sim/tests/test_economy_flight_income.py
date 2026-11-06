"""The income a worker of an area is taken to earn when judging flight is the area's wages weighted by the people working each
trade, so a trade nobody works does not set it. `mean_year_income` is called on a market state written out here."""
QUICK_TOPIC = True

import unittest

from sim.economy.flight_step import add_returners, mean_year_income
from sim.labour.api import MarketState


def state(wages, workers):
    market = MarketState()
    market.wages = wages
    market.workers = workers
    return market


class MeanYearIncome(unittest.TestCase):
    def test_wages_are_weighted_by_the_people_working_each_trade(self):
        market = state({"north": {"smith": 3.0, "weaver": 1.0, "idle": 100.0}},
                       {"north": {"smith": [1.0, 1.0], "weaver": [6.0], "idle": []}})
        self.assertAlmostEqual(mean_year_income(market, 10.0)["north"], 10.0 * (3.0 * 2.0 + 1.0 * 6.0) / 8.0)

    def test_with_nobody_working_it_is_the_plain_mean(self):
        market = state({"north": {"smith": 3.0, "weaver": 1.0}}, {})
        self.assertAlmostEqual(mean_year_income(market, 10.0)["north"], 20.0)

    def test_an_area_with_no_wages_has_no_income(self):
        self.assertEqual(mean_year_income(state({"north": {}}, {}), 10.0), {})


class AddReturners(unittest.TestCase):
    def test_returners_to_an_area_with_no_workers_after_the_market_are_a_move_into_it(self):
        migrated = {"north": -1.0}
        add_returners(migrated, {"north": 5.0}, {"north": 5.0, "south": 3.0})
        self.assertEqual(migrated, {"north": -1.0, "south": 3.0})

    def test_the_people_who_left_a_refuge_are_a_move_out_of_it(self):
        migrated = {}
        add_returners(migrated, {"refuge": 10.0, "home": 2.0}, {"refuge": 7.0, "home": 5.0})
        self.assertEqual(migrated, {"refuge": -3.0, "home": 3.0})


if __name__ == "__main__":
    unittest.main()
