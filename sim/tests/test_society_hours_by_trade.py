"""`society_hours_by_trade`: the hours a society's workers give, from the labour core's people. Plain function, no game."""
import unittest

from sim.labour import api as labour_api

QUICK_TOPIC = True

REGISTRY = {"fisher": {"family": "primary", "gathers_food_sources": ["marine_fishing"], "food_kcal_per_hour": 1000.0},
            "smith": {"family": "craft"}}


class SocietyHoursByTradeTests(unittest.TestCase):
    def test_each_trade_gives_its_people_times_the_hours_of_a_person_year(self):
        hours = labour_api.society_hours_by_trade({"fisher": 10.0, "smith": 2.5}, 2000.0)
        self.assertEqual(hours, {"fisher": 20000.0, "smith": 5000.0})

    def test_a_trade_with_no_people_is_left_out(self):
        self.assertEqual(labour_api.society_hours_by_trade({"fisher": 0.0, "smith": 1.0}, 100.0), {"smith": 100.0})

    def test_nothing_is_booked_while_the_agent_economy_opens(self):
        self.assertEqual(labour_api.society_hours_by_trade(None, 2000.0), {})
        self.assertEqual(labour_api.society_hours_by_trade({"fisher": 3.0}, None), {})

    def test_the_hours_open_the_gathering_cap_that_empty_hours_close(self):
        closed = labour_api.hours_cap_kcal(labour_api.society_hours_by_trade({}, 2000.0), REGISTRY)
        opened = labour_api.hours_cap_kcal(labour_api.society_hours_by_trade({"fisher": 10.0}, 2000.0), REGISTRY)
        self.assertEqual(closed["marine_fishing"], 0.0)
        self.assertEqual(opened["marine_fishing"], 2.0e7)

    def test_the_occupational_table_is_not_empty_once_hours_are_booked(self):
        hours = labour_api.society_hours_by_trade({"fisher": 10.0, "smith": 2.5}, 2000.0)
        table = labour_api.hours_by_trade(hours, {}, frozenset(), "smith")
        self.assertEqual(table, {"fisher": 20000.0, "smith": 5000.0})
        self.assertAlmostEqual(sum(labour_api.shares_by_group(table).values()), 1.0)


if __name__ == "__main__":
    unittest.main()
