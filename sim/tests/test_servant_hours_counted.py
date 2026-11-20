"""servant_hours_counted: the hired household work a household's next plan starts from and counts on being served."""

QUICK_TOPIC = True

import unittest

from sim.economy import household_work_year
from sim.economy.servant_hours_counted import as_planned, as_served

YEAR = 2000.0


class AsPlanned(unittest.TestCase):
    def test_the_plan_starts_from_last_years_plan_and_counts_on_whatever_it_plans(self):
        self.assertEqual(as_planned(500.0, 500.0), (500.0, None))
        self.assertEqual(as_planned(500.0, 0.0), (500.0, None))


class AsServed(unittest.TestCase):
    def test_served_in_full_it_starts_from_and_counts_on_the_plan(self):
        self.assertEqual(as_served(500.0, 0.0), (500.0, 500.0))

    def test_served_in_part_it_starts_from_and_counts_on_the_part_served(self):
        self.assertEqual(as_served(500.0, 320.0), (180.0, 180.0))

    def test_served_nothing_it_starts_from_and_counts_on_nothing(self):
        self.assertEqual(as_served(500.0, 500.0), (0.0, 0.0))

    def test_going_without_more_than_it_planned_is_still_nothing_served(self):
        # a cohort that hired nothing keeps the need's whole floor, so the hours it went without can exceed its plan
        self.assertEqual(as_served(0.0, 900.0), (0.0, 0.0))
        self.assertEqual(as_served(500.0, 900.0), (0.0, 0.0))

    def test_a_figure_under_nothing_counts_as_nothing(self):
        self.assertEqual(as_served(500.0, -3.0), (500.0, 500.0))


class PlannedHoursCountingOnWhatWasServed(unittest.TestCase):
    """10000 hours needed; an hour of its own is worth far more than a servant costs, so it wants to hire all it can."""
    NEEDED, VALUE, PRICE = 10000.0, 100.0, 1.0

    def planned(self, previous_hired, counted_on):
        return household_work_year.planned_hours(self.NEEDED, self.VALUE, self.PRICE, 0.0, (), None, previous_hired, counted_on)

    def test_counting_on_whatever_it_plans_its_own_hours_are_the_work_less_the_plan(self):
        hired, own, _ground = self.planned(2000.0, None)
        self.assertGreater(hired, 2000.0)
        self.assertAlmostEqual(own, self.NEEDED - hired)

    def test_counting_on_what_it_was_served_its_own_hours_are_the_work_less_that(self):
        hired, own, _ground = self.planned(2000.0, 2000.0)
        self.assertGreater(hired, 2000.0)                    # it still bids for more servants than it had
        self.assertAlmostEqual(own, self.NEEDED - 2000.0)     # and keeps the hours for the work those have not yet done

    def test_served_nothing_it_keeps_the_hours_for_all_the_work(self):
        hired, own, _ground = self.planned(0.0, 0.0)
        self.assertGreater(hired, 0.0)
        self.assertAlmostEqual(own, self.NEEDED)

    def test_planning_fewer_than_it_was_served_it_counts_on_the_plan(self):
        # servants cost more than its own hour is worth: it wants none, and steps down from the 6000 it was served
        hired, own, _ground = household_work_year.planned_hours(self.NEEDED, 1.0, 100.0, 0.0, (), None, 6000.0, 6000.0)
        self.assertLess(hired, 6000.0)
        self.assertAlmostEqual(own, self.NEEDED - hired)


if __name__ == "__main__":
    unittest.main()
