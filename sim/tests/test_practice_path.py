"""Complaint 473, owner question 6: the learning path of a crew (`practice_path.learning_path_scales`) is the discounted mean over the
horizon of the hours multiplier and the usable share, and `entry_practice.planned_recipe` takes the same hours for the same crew,
horizon and rate. Each test calls one function with its inputs written out."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import entry_practice, practice, practice_path
from sim.economy.types import Recipe

BOOKED = {"hand": 4.0}


def scales(units, pace, horizon, rate):
    return practice_path.learning_path_scales(units, BOOKED, pace, horizon, rate)


def hand_mean(start_units, pace, horizon, rate):
    """The discounted mean of the hours multiplier, each year's units written out from the start."""
    weights = [(1.0 + rate) ** -year for year in range(horizon)]
    multipliers = [practice.hours_multiplier(start_units + pace * year) for year in range(horizon)]
    return sum(weight * multiplier for weight, multiplier in zip(weights, multipliers)) / sum(weights)


class LearningPathScales(unittest.TestCase):
    def test_it_is_the_discounted_mean_of_each_years_multiplier(self):
        found, _share = scales({"hand": 1.0}, 10.0, 20, 0.05)
        self.assertAlmostEqual(found["hand"], hand_mean(1.0, 10.0, 20, 0.05), places=9)

    def test_a_new_crews_multiplier_lies_between_one_and_this_years(self):
        found, _share = scales({"hand": 1.0}, 10.0, 20, 0.05)
        self.assertGreater(found["hand"], 1.0)
        self.assertLess(found["hand"], practice.hours_multiplier(1.0))

    def test_a_crew_at_the_floor_gives_exactly_one_for_both(self):
        found, share = scales({}, 10.0, 20, 0.05)
        self.assertEqual(found, {"hand": 1.0})
        self.assertEqual(share, 1.0)

    def test_a_faster_pace_gives_a_lower_multiplier(self):
        slow, _ = scales({"hand": 1.0}, 3.0, 20, 0.05)
        middle, _ = scales({"hand": 1.0}, 10.0, 20, 0.05)
        fast, _ = scales({"hand": 1.0}, 50.0, 20, 0.05)
        self.assertGreater(slow["hand"], middle["hand"])
        self.assertGreater(middle["hand"], fast["hand"])

    def test_a_higher_discount_rate_gives_a_higher_multiplier(self):
        low, _ = scales({"hand": 1.0}, 10.0, 20, 0.05)
        high, _ = scales({"hand": 1.0}, 10.0, 20, 0.20)
        self.assertGreater(high["hand"], low["hand"])

    def test_one_per_cent_more_pace_moves_the_multiplier_by_less_than_one_per_cent(self):
        base, _ = scales({"hand": 1.0}, 10.0, 20, 0.05)
        more, _ = scales({"hand": 1.0}, 10.1, 20, 0.05)
        self.assertLess(abs(more["hand"] - base["hand"]) / base["hand"], 0.01)

    def test_a_one_year_horizon_gives_this_years_multiplier_and_share(self):
        found, share = scales({"hand": 1.0}, 10.0, 1, 0.05)
        self.assertAlmostEqual(found["hand"], practice.hours_multiplier(1.0), places=12)
        self.assertAlmostEqual(share, practice.usable_output_share(4.0, 4.0 * practice.hours_multiplier(1.0)), places=12)

    def test_the_share_is_between_this_years_and_one_for_a_new_crew(self):
        _found, share = scales({"hand": 1.0}, 10.0, 20, 0.05)
        self.assertGreater(share, practice.usable_output_share(4.0, 4.0 * practice.hours_multiplier(1.0)))
        self.assertLess(share, 1.0)


class HorizonYears(unittest.TestCase):
    def test_a_recipe_with_no_plant_keeps_the_expected_years(self):
        self.assertEqual(practice_path.horizon_years(0.0), int(practice_path.YEARS_A_WORKSHOP_EXPECTS_TO_KEEP_A_TRADE))

    def test_a_plant_that_wears_out_sooner_holds_it(self):
        self.assertEqual(practice_path.horizon_years(7.0), 7)

    def test_a_plant_that_outlives_the_expected_years_does_not_stretch_it(self):
        self.assertEqual(practice_path.horizon_years(1.0e6), int(practice_path.YEARS_A_WORKSHOP_EXPECTS_TO_KEEP_A_TRADE))


class PlannedRecipeIsThePath(unittest.TestCase):
    def test_the_entry_hours_are_the_booked_hours_times_the_paths_multiplier(self):
        recipe = Recipe("mine_salt", {"salt": 10.0}, {}, {"hand": 4.0})
        planned = entry_practice.planned_recipe(recipe, [], 10.0, 0.05)
        horizon = practice_path.horizon_years(recipe.plant_life_years)
        self.assertTrue(math.isclose(planned.labour_hours["hand"], 4.0 * hand_mean(1.0, 10.0, horizon, 0.05), rel_tol=1e-9))

    def test_a_crew_at_the_floor_needs_the_booked_recipe_itself(self):
        recipe = Recipe("mine_salt", {"salt": 10.0}, {}, {"hand": 4.0})
        self.assertIs(entry_practice.planned_recipe(recipe, [{}, {}], 10.0, 0.05), recipe)


if __name__ == "__main__":
    unittest.main()
