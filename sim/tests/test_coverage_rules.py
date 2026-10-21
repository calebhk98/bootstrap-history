"""Complaint 190 and 640: the coverage, disease-burden and roll-out rules on plain inputs, no game."""

QUICK_TOPIC = True

import unittest

from sim.engine import coverage_rules as rules


class Coverage(unittest.TestCase):
    def test_a_unit_serves_its_staff_hours_over_the_hours_each_person_needs(self):
        self.assertEqual(rules.people_per_unit(4000.0, 8.0), 500.0)

    def test_eligible_people_are_the_population_times_the_share(self):
        self.assertEqual(rules.people_who_can_use(1000.0, 0.25), 250.0)

    def test_eligible_people_are_never_below_one(self):
        self.assertEqual(rules.people_who_can_use(0.0, 0.25), 1.0)

    def test_a_shut_work_covers_nothing(self):
        self.assertEqual(rules.coverage_share(False, 10.0, 100.0, 1000.0), 0.0)

    def test_open_units_cover_their_people_over_the_eligible(self):
        self.assertAlmostEqual(rules.coverage_share(True, 2.0, 100.0, 1000.0), 0.2)

    def test_a_work_cannot_cover_more_than_everyone(self):
        self.assertEqual(rules.coverage_share(True, 1.0e6, 100.0, 1000.0), 1.0)

    def test_units_for_a_share_serve_that_share(self):
        units = rules.units_for_coverage(0.5, 1000.0, 100.0)
        self.assertAlmostEqual(units, 5.0)
        self.assertAlmostEqual(rules.coverage_share(True, units, 100.0, 1000.0), 0.5)


class Rollout(unittest.TestCase):
    def test_nothing_open_opens_the_whole_want(self):
        self.assertEqual(rules.rollout_units(7.0, 0.0), 7.0)

    def test_something_open_opens_only_what_is_still_wanted(self):
        self.assertEqual(rules.rollout_units(7.0, 3.0), 4.0)

    def test_a_want_within_the_minimum_of_what_is_open_is_already_covered(self):
        self.assertIsNone(rules.rollout_units(3.01, 3.0))
        self.assertIsNone(rules.rollout_units(2.0, 3.0))

    def test_a_want_just_past_the_minimum_opens(self):
        self.assertAlmostEqual(rules.rollout_units(3.03, 3.0), 0.03)


class DiseaseBurden(unittest.TestCase):
    PRE = 0.9

    def burden(self, weights, held):
        return rules.disease_burden(weights, lambda technology: held.get(technology, 0.0), self.PRE)

    def test_nothing_held_is_the_full_burden(self):
        self.assertEqual(self.burden({"a": 1.0, "b": 3.0}, {}), 1.0)

    def test_everything_held_is_no_burden(self):
        self.assertEqual(self.burden({"a": 1.0, "b": 3.0}, {"a": 1.0, "b": 1.0}), 0.0)

    def test_a_half_covered_work_takes_half_its_weight_off(self):
        self.assertAlmostEqual(self.burden({"a": 1.0, "b": 3.0}, {"b": 0.5}), 1.0 - 1.5 / 4.0)

    def test_no_weight_at_all_leaves_the_pre_industrial_burden(self):
        self.assertEqual(self.burden({}, {}), self.PRE)
        self.assertEqual(self.burden({"a": 0.0}, {"a": 1.0}), self.PRE)

    def test_the_result_is_clamped_to_the_unit_range(self):
        self.assertEqual(self.burden({"a": 1.0}, {"a": 2.0}), 0.0)
        self.assertEqual(self.burden({"a": 1.0}, {"a": -1.0}), 1.0)


if __name__ == "__main__":
    unittest.main()
