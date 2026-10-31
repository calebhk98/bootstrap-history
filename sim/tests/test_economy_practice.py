"""Complaint 644: a producer's crew learns on the job. Plain functions on written-out numbers."""
QUICK_TOPIC = True

import unittest

from sim.economy import practice, producers
from sim.economy.types import Recipe

FLOOR = practice.SOURCE_TASK_FLOOR_FRACTION
FARM = Recipe("farm", {"grain": 1.0}, {}, {"hand": 10.0})


def farmer(**fields):
    return producers.Producer("p", "owner", "farm", "tile", 100.0, **fields)


class PracticeTests(unittest.TestCase):
    def test_an_established_crew_needs_the_booked_hours(self):
        self.assertAlmostEqual(practice.hours_multiplier(practice.established_units()), 1.0)

    def test_a_first_attempt_needs_the_floors_inverse_in_hours(self):
        self.assertAlmostEqual(practice.hours_multiplier(1.0), 1.0 / FLOOR)

    def test_hours_fall_with_runs_made(self):
        self.assertLess(practice.hours_multiplier(20.0), practice.hours_multiplier(5.0))

    def test_hours_never_go_below_the_booked(self):
        self.assertEqual(practice.hours_multiplier(1.0e12), 1.0)

    def test_runs_add_to_the_crews_units(self):
        self.assertEqual(practice.units_after_year(10.0, 7.0, 0.0, 10.0), 17.0)

    def test_hired_hands_bring_the_pools_practice_and_close_part_of_the_gap(self):
        self.assertEqual(practice.units_after_year(100.0, 0.0, 0.5, 0.0, 0.5), 75.0)

    def test_layoffs_leave_the_stayers_practice(self):
        self.assertEqual(practice.hired_share(100.0, 40.0), 0.0)

    def test_growth_is_hired(self):
        self.assertEqual(practice.hired_share(50.0, 100.0), 0.5)

    def test_a_first_year_hires_nobody(self):
        self.assertEqual(practice.hired_share(-1.0, 100.0), 0.0)

    def test_an_entrant_starts_at_the_mean_of_the_recipes_other_producers(self):
        self.assertEqual(practice.entrant_units([10.0, 30.0]), 20.0)

    def test_an_entrant_with_no_peers_makes_a_first_attempt(self):
        self.assertEqual(practice.entrant_units([]), 1.0)

    def test_a_crew_at_the_floor_is_dropped_from_the_record(self):
        self.assertEqual(practice.crew_runs_after_year({"hand": 1.0e9}, 1.0, 0.0, {}), {})

    def test_a_crew_still_learning_gains_the_years_runs(self):
        self.assertEqual(practice.crew_runs_after_year({"hand": 2.0}, 3.0, 0.0, {}), {"hand": 5.0})

    def test_an_entrant_into_an_established_recipe_starts_at_the_floor(self):
        self.assertEqual(practice.entrant_crew_runs(FARM, [{}, {}]), {})

    def test_an_entrant_into_a_new_recipe_starts_at_a_first_attempt(self):
        self.assertEqual(practice.entrant_crew_runs(FARM, []), {"hand": 1.0})

    def test_a_trade_with_no_entry_keeps_the_booked_recipe(self):
        self.assertIs(practice.recipe_for(FARM, {}), FARM)

    def test_a_novice_crews_recipe_books_more_hours(self):
        self.assertAlmostEqual(practice.recipe_for(FARM, {"hand": 1.0}).labour_hours["hand"], 10.0 / FLOOR)

    def test_a_novice_crew_makes_fewer_runs_from_the_same_hours(self):
        achieved, _moves = producers.produce(farmer(crew_runs={"hand": 1.0}), FARM, {}, {"hand": 100.0}, 10.0)
        self.assertAlmostEqual(achieved, 100.0 / (10.0 / FLOOR))

    def test_an_established_crew_makes_the_booked_runs(self):
        achieved, _moves = producers.produce(farmer(), FARM, {}, {"hand": 100.0}, 10.0)
        self.assertAlmostEqual(achieved, 10.0)


if __name__ == "__main__":
    unittest.main()
