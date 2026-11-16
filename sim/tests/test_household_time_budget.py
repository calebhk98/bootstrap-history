"""Household work is drawn from the labour year's own days, and hiring servants is continuous in the budget and changes gradually (Complaint 473)."""

QUICK_TOPIC = True

import unittest

from sim.economy import household_servants, households_work

DATA = {"days_per_year": 365, "cooking_fuel_mj_per_person_per_day": 20.0, "tasks": {
    "carrying": {"needs_hearth": False, "hours_per_adult_woman_per_day": 2.0, "adult_women_per_person": 0.25},
    "cooking": {"needs_hearth": True, "hours_per_person_per_day": 0.5},
}}
YEAR = 2000.0


class WorkingDaysTests(unittest.TestCase):
    def test_hours_are_hours_per_day_times_the_working_days_passed_in(self):
        # carrying: 2.0 * 0.25 = 0.5 hours a day; cooking: 0.5 hours a day; over 200 working days
        self.assertAlmostEqual(households_work.hours_per_person_per_year(DATA, 200.0), 200.0)

    def test_doubling_the_working_days_doubles_the_hours(self):
        self.assertAlmostEqual(households_work.hours_per_person_per_year(DATA, 400.0),
                               2.0 * households_work.hours_per_person_per_year(DATA, 200.0))

    def test_the_civil_year_of_the_data_does_not_enter_the_hours(self):
        other = dict(DATA, days_per_year=100)
        self.assertAlmostEqual(households_work.hours_per_person_per_year(other, 200.0),
                               households_work.hours_per_person_per_year(DATA, 200.0))

    def test_cooking_fuel_still_follows_the_civil_year(self):
        self.assertAlmostEqual(households_work.cooking_fuel_per_person_per_year(DATA), 20.0 * 365)

    def test_hours_needed_passes_the_working_days_through(self):
        self.assertAlmostEqual(households_work.hours_needed(10.0, DATA, 200.0), 2000.0)


class HiringBudgetTests(unittest.TestCase):
    COST = 2000.0   # service price 1.0 over a servant's year

    def hired(self, budget):
        return household_servants.hired_hours_whole(1000.0, 1.0, 100.0, 1.0, budget, YEAR)

    def test_a_budget_a_hair_below_and_above_the_cost_hires_nearly_the_same(self):
        self.assertAlmostEqual(self.hired(self.COST - 0.01), self.hired(self.COST + 0.01), delta=0.01 * 1000.0)

    def test_hours_rise_with_the_budget(self):
        hours = [self.hired(budget) for budget in (500.0, 1500.0, 2000.0, 2600.0, 4000.0)]
        self.assertEqual(hours, sorted(hours))
        self.assertLess(hours[0], hours[-1])

    def test_an_unknown_budget_is_no_bound(self):
        self.assertGreater(self.hired(None), self.hired(self.COST))

    def test_a_budget_of_zero_or_less_hires_none(self):
        self.assertEqual(self.hired(0.0), 0.0)
        self.assertEqual(self.hired(-5.0), 0.0)


class AdjustedHiringTests(unittest.TestCase):
    def test_closes_the_declared_share_of_the_gap_upward(self):
        self.assertAlmostEqual(households_work.adjusted_hired_hours(100.0, 200.0, 1000.0, 0.2), 120.0)

    def test_closes_the_declared_share_of_the_gap_downward(self):
        self.assertAlmostEqual(households_work.adjusted_hired_hours(200.0, 100.0, 1000.0, 0.2), 180.0)

    def test_the_default_share_is_the_declared_one(self):
        self.assertAlmostEqual(households_work.adjusted_hired_hours(0.0, 100.0, 1000.0),
                               households_work.SERVANT_HIRING_ADJUSTMENT_SHARE_PER_YEAR * 100.0)

    def test_never_above_the_hours_needed(self):
        self.assertEqual(households_work.adjusted_hired_hours(900.0, 5000.0, 50.0, 0.5), 50.0)

    def test_never_below_zero(self):
        self.assertEqual(households_work.adjusted_hired_hours(-10.0, 0.0, 1000.0, 0.5), 0.0)
