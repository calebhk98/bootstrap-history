"""Household work as a need (Complaint 645): hours from the data file, own or hired, and cooked food without a hearth."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.economy import households_work
from sim.economy.households_basket import make_basket
from sim.world import need_basket

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

DATA = {"days_per_year": 100, "tasks": {
    "carrying": {"needs_hearth": False, "hours_per_adult_woman_per_day": 2.0, "adult_women_per_person": 0.25},
    "cooking": {"needs_hearth": True, "hours_per_person_per_day": 0.5},
}}
NEED_DATA = {"needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 10.0}},
             "goods": {"wheat_kg": {"satisfies": {"food": 1.0}},
                       "cooked_meal_kg": {"satisfies": {"food": 0.3}, "ready_to_eat": True}}}


class HoursTests(unittest.TestCase):
    def test_hours_follow_the_figures_of_the_data(self):
        # carrying: 2 hours * 0.25 * 100 days = 50; cooking: 0.5 * 100 = 50
        self.assertAlmostEqual(households_work.hours_per_person_per_year(DATA), 100.0)
        self.assertAlmostEqual(households_work.hours_needed(30.0, DATA), 3000.0)

    def test_a_household_without_a_hearth_does_no_cooking_of_its_own(self):
        self.assertAlmostEqual(households_work.hours_per_person_per_year(DATA, has_hearth=False), 50.0)

    def test_the_needs_file_satiation_equals_the_hours_of_the_data_file(self):
        data = households_work.load_household_work()
        with open(os.path.join(ROOT, "data", "world", "needs.json"), encoding="utf-8") as handle:
            need = json.load(handle)["needs"]["household_work"]
        self.assertAlmostEqual(need["satiation_per_capita_per_year"], households_work.hours_per_person_per_year(data))


class HiringTests(unittest.TestCase):
    def test_a_richer_cohort_hires_more_at_the_same_wage(self):
        needed = households_work.hours_needed(100.0, DATA)
        poor = households_work.hired_hours(needed, 500.0, 2.0, 0.1)
        rich = households_work.hired_hours(needed, 5000.0, 2.0, 0.1)
        self.assertGreater(rich, poor)
        self.assertAlmostEqual(poor, 25.0)

    def test_nobody_hires_more_than_the_work_there_is(self):
        self.assertAlmostEqual(households_work.hired_hours(40.0, 1e9, 2.0, 0.1), 40.0)

    def test_a_cohort_with_no_surplus_hires_none_and_does_it_all_itself(self):
        hired = households_work.hired_hours(1000.0, 0.0, 2.0, 0.1)
        self.assertEqual(hired, 0.0)
        self.assertEqual(households_work.own_hours(1000.0, hired), 1000.0)

    def test_own_hours_are_the_work_less_the_hired(self):
        self.assertAlmostEqual(households_work.own_hours(1000.0, 250.0), 750.0)


class CookedFoodTests(unittest.TestCase):
    def _shares(self, basket):
        priced = need_basket.need_prices(basket, {"wheat_kg": 1.0, "cooked_meal_kg": 1.0}.get)
        return {good: share for good, _price, _effect, share in priced[0].goods}

    def test_a_cohort_without_a_hearth_buys_cooked_food(self):
        basket = make_basket(NEED_DATA, {})
        ready = households_work.ready_to_eat_goods(NEED_DATA)
        shares = self._shares(households_work.without_hearth_basket(basket, ready))
        self.assertEqual(set(shares), {"cooked_meal_kg"})
        self.assertIn("wheat_kg", self._shares(basket))

    def test_the_whole_food_floor_is_bought_cooked_without_a_hearth(self):
        self.assertAlmostEqual(households_work.cooked_food_units(20.0, 10.0, False), 200.0)
        self.assertEqual(households_work.cooked_food_units(20.0, 10.0, True), 0.0)

    def test_a_basket_with_no_ready_food_is_left_whole(self):
        basket = make_basket(NEED_DATA, {})
        self.assertEqual(households_work.without_hearth_basket(basket, frozenset()), basket)


if __name__ == "__main__":
    unittest.main()
