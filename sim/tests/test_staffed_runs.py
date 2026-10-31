"""Runs the hired hours staff: the scarcest trade sets them; a recipe without hired hours has none."""
QUICK_TOPIC = True

import unittest

from sim.economy.staffed_runs import change_anchor, staffed_runs


class StaffedRunsTest(unittest.TestCase):
    def test_the_scarcest_trade_sets_the_runs(self):
        self.assertEqual(staffed_runs({"miller": 10.0, "carter": 2.0}, {"miller": 500.0, "carter": 400.0}), 50.0)

    def test_a_trade_with_no_hours_hired_staffs_nothing(self):
        self.assertEqual(staffed_runs({"miller": 10.0, "carter": 2.0}, {"miller": 500.0}), 0.0)

    def test_a_recipe_without_hired_hours_has_no_staffed_runs(self):
        self.assertIsNone(staffed_runs({}, {"miller": 500.0}))

    def test_the_anchor_is_the_larger_of_worked_and_staffed_runs(self):
        self.assertEqual(change_anchor(20.0, 50.0), 50.0)
        self.assertEqual(change_anchor(60.0, 50.0), 60.0)


class YearsChangeTest(unittest.TestCase):
    def test_a_crew_that_stayed_while_inputs_failed_lets_the_plan_stay_high(self):
        from sim.economy.producers import Producer, within_a_years_change
        producer = Producer("p", "o", "r", "t", capacity_runs=100.0, last_runs=20.0, staffed_runs=80.0)
        self.assertEqual(within_a_years_change(producer, 100.0), 100.0)      # 80 staffed + 25 a year's change
        unstaffed = Producer("p", "o", "r", "t", capacity_runs=100.0, last_runs=20.0)
        self.assertEqual(within_a_years_change(unstaffed, 100.0), 45.0)


if __name__ == "__main__":
    unittest.main()
