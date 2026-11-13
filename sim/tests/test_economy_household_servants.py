"""Whole servants and the urban marker (Complaint 645)."""

QUICK_TOPIC = True

import unittest

from sim.economy import household_servants, household_urban, household_work_year

YEAR = 2000.0


class WholeServantTests(unittest.TestCase):
    def test_a_household_too_poor_for_one_whole_servant_hires_none_rather_than_a_fraction(self):
        # a servant's year costs 1.0 * 2000 = 2000; the household has 1500; its hour is worth 100 so hiring would pay
        hired = household_servants.hired_hours_whole(1000.0, 1.0, 100.0, 1.0, 1500.0, YEAR)
        self.assertEqual(hired, 0.0)

    def test_the_same_household_with_the_price_of_a_servant_hires(self):
        self.assertGreater(household_servants.hired_hours_whole(1000.0, 1.0, 100.0, 1.0, 2000.0, YEAR), 900.0)

    def test_a_servant_frees_no_more_hours_than_the_household_has_of_work(self):
        hired = household_servants.hired_hours_whole(1000.0, 1.0, 1e9, 1.0, 1e9, YEAR)
        self.assertAlmostEqual(hired, 1000.0)

    def test_work_too_light_to_repay_a_servants_year_is_not_hired(self):
        # 100 hours freed at 1.5 each is worth 150 against a year's cost of 2000
        self.assertLess(household_servants.hired_hours_whole(100.0, 1.0, 1.5, 1.0, None, YEAR), 1e-6)

    def test_an_unknown_budget_is_no_bound(self):
        self.assertGreater(household_servants.hired_hours_whole(1000.0, 1.0, 100.0, 1.0, None, YEAR), 900.0)

    def test_nothing_is_hired_where_the_service_has_no_price(self):
        self.assertEqual(household_servants.hired_hours_whole(1000.0, 1.0, 100.0, 0.0, 1e9, YEAR), 0.0)


class UrbanMarkerTests(unittest.TestCase):
    def test_a_tile_where_most_people_work_no_land_is_urban(self):
        self.assertTrue(household_urban.is_urban([(70.0, 0.0), (30.0, 0.4)], 0.5))

    def test_a_tile_where_most_people_work_land_is_not(self):
        self.assertFalse(household_urban.is_urban([(30.0, 0.0), (70.0, 0.4)], 0.5))

    def test_a_tile_with_no_people_is_not_urban(self):
        self.assertFalse(household_urban.is_urban([], 0.5))
        self.assertFalse(household_urban.is_urban([(0.0, 0.0)], 0.5))


class PlannedHoursTests(unittest.TestCase):
    def test_a_cohort_whose_households_cannot_pay_a_servants_year_does_its_own_work(self):
        # 10 households needing 1000 hours each, an hour worth 100, a servant's year costing 2000 and a household income of 1500
        hired, own, _milled = household_work_year.planned_hours(10000.0, 100.0, 1.0, 0.0, (), (10.0, 1500.0, YEAR))
        self.assertEqual(hired, 0.0)
        self.assertEqual(own, 10000.0)

    def test_with_no_servant_year_in_the_data_hiring_stays_divisible(self):
        hired, _own, _milled = household_work_year.planned_hours(100.0, 2.0, 2.0, 0.0, ())
        self.assertAlmostEqual(hired, 50.0)


if __name__ == "__main__":
    unittest.main()
