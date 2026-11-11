"""The hours a plot takes given the tools, team and plant a household holds (plot_means.py), and own-plot growing and
its hours plan reading them: a short means asks more hours for the same crop and never stops it."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import plot_means
from sim.economy.households_cohort import Cohort
from sim.economy.households_own import hours_for_own_plan, own_production
from sim.economy.types import Recipe, ToolFallback

BY_HAND = ToolFallback("", 0.0, 2.0, ("hand",))      # working by hand takes twice the hours
TOOLED = Recipe("grow_grain", {"grain": 10.0}, {"hoe": 1.0}, {"hand": 4.0}, tool_wear={"hoe": 1.0},
                tool_fallbacks={"hoe": (BY_HAND,)})
PLOUGHED = Recipe("grow_grain", {"grain": 10.0}, {"hoe": 1.0}, {"hand": 4.0}, plant_goods={"ox": 2.0}, tool_wear={"hoe": 1.0},
                  tool_fallbacks={"hoe": (BY_HAND,)})
OPTIONS = {"food": [(0.4, "grow_grain", "grain", 1.0)]}      # four hours make ten units: 0.4 an hour a unit
BASKET = types.SimpleNamespace(needs=[types.SimpleNamespace(need_id="food", subsistence_per_person=1.0, goods=(("grain", 1.0),))])
LAND = {"grow_grain": 2.0}
PEOPLE = Cohort("household:t:0", "t", 0, 10.0, 5.0, 0.0, own_plan_by_need={"food": 10.0})


class HoursForRunsTests(unittest.TestCase):
    def test_a_held_tool_leaves_the_recipes_hours(self):
        self.assertAlmostEqual(plot_means.hours_for_runs(TOOLED, {"hoe": 10.0}, 5.0), 20.0)

    def test_no_tool_works_by_hand_at_double_the_hours(self):
        self.assertAlmostEqual(plot_means.hours_for_runs(TOOLED, {"hoe": 0.0}, 5.0), 40.0)

    def test_half_the_tools_double_half_the_runs(self):
        self.assertAlmostEqual(plot_means.hours_for_runs(TOOLED, {"hoe": 2.5}, 5.0), 30.0)

    def test_runs_beyond_the_team_held_are_worked_by_hand(self):
        # five runs need ten oxen; five are held: two and a half runs are covered, two and a half are by hand (four extra hours each)
        held = {"hoe": 10.0, "ox": 5.0}
        self.assertAlmostEqual(plot_means.hours_for_runs(PLOUGHED, held, 5.0), 20.0 + 2.5 * 4.0)

    def test_a_team_held_in_full_adds_no_hours(self):
        self.assertAlmostEqual(plot_means.hours_for_runs(PLOUGHED, {"hoe": 10.0, "ox": 10.0}, 5.0), 20.0)

    def test_a_recipe_with_no_by_hand_step_takes_its_own_hours_whatever_the_plant_held(self):
        plain = Recipe("grow_grain", {"grain": 10.0}, {}, {"hand": 4.0}, plant_goods={"ox": 2.0})
        self.assertAlmostEqual(plot_means.hours_for_runs(plain, {}, 5.0), 20.0)

    def test_the_runs_hours_can_work_invert_the_hours_the_runs_take(self):
        for held in ({"hoe": 10.0, "ox": 10.0}, {"hoe": 2.5, "ox": 1.0}, {}):
            runs = plot_means.runs_within(PLOUGHED, held, 37.0)
            self.assertAlmostEqual(plot_means.hours_for_runs(PLOUGHED, held, runs), 37.0, places=6)

    def test_means_goods_lists_tools_fallbacks_and_plant(self):
        recipe = Recipe("r", {"grain": 1.0}, {"hoe": 1.0}, {"hand": 1.0}, plant_goods={"ox": 1.0}, tool_wear={"hoe": 1.0},
                        tool_fallbacks={"hoe": (ToolFallback("stick", 1.0, 1.5, ("hand",)), BY_HAND)})
        self.assertEqual(plot_means.means_goods(recipe), frozenset({"hoe", "stick", "ox"}))


class OwnProductionWithMeansTests(unittest.TestCase):
    def grow(self, held, idle=1000.0, recipe=TOOLED, hectares=100.0):
        hours = {}
        _moves, grown, units = own_production(PEOPLE, idle, OPTIONS, {"grow_grain": recipe}, 1.0, BASKET, LAND, hectares, hours,
                                              held)
        return grown, units, hours

    def test_a_cohort_that_loses_its_tool_works_more_hours_for_the_same_crop(self):
        _grown, units_tooled, hours_tooled = self.grow({"hoe": 100.0})
        _grown, units_bare, hours_bare = self.grow({"hoe": 0.0})
        self.assertAlmostEqual(units_tooled["food"], 10.0)
        self.assertAlmostEqual(units_bare["food"], 10.0)
        self.assertAlmostEqual(hours_tooled["grow_grain"], 4.0)        # ten units at 0.4 an hour: one run
        self.assertAlmostEqual(hours_bare["grow_grain"], 8.0)

    def test_with_hours_short_the_bare_cohort_grows_less_not_nothing(self):
        _grown, units, hours = self.grow({"hoe": 0.0}, idle=4.0)
        self.assertAlmostEqual(hours["grow_grain"], 4.0)
        self.assertAlmostEqual(units["food"], 5.0)

    def test_no_stock_given_means_taken_as_held(self):
        _moves, _grown, units = own_production(PEOPLE, 1000.0, OPTIONS, {"grow_grain": TOOLED}, 1.0, BASKET, LAND, 100.0)
        self.assertAlmostEqual(units["food"], 10.0)

    def test_a_cohort_without_the_team_works_the_plough_crop_by_hand(self):
        _grown, units, hours = self.grow({"hoe": 100.0, "ox": 0.0}, recipe=PLOUGHED)
        self.assertAlmostEqual(units["food"], 10.0)
        self.assertAlmostEqual(hours["grow_grain"], 8.0)

    def test_the_land_worked_follows_the_runs_not_the_extra_hours(self):
        # ten units are one run of two hectares, whatever the hours the missing tool added
        _grown, units, _hours = self.grow({"hoe": 0.0}, hectares=2.0)
        self.assertAlmostEqual(units["food"], 10.0)
        _grown, units, _hours = self.grow({"hoe": 0.0}, hectares=1.0)
        self.assertAlmostEqual(units["food"], 5.0)


class OwnPlanHoursWithMeansTests(unittest.TestCase):
    RECIPES = {"grow_grain": TOOLED}

    def plan_hours(self, held):
        return hours_for_own_plan(PEOPLE, OPTIONS, 1.0, self.RECIPES, LAND, 100.0, held)

    def test_a_short_tool_adds_the_by_hand_hours_to_the_plan(self):
        self.assertAlmostEqual(self.plan_hours({"hoe": 100.0}), 4.0)
        self.assertAlmostEqual(self.plan_hours({"hoe": 0.0}), 8.0)

    def test_no_stock_given_leaves_the_plan_hours(self):
        self.assertAlmostEqual(hours_for_own_plan(PEOPLE, OPTIONS, 1.0, self.RECIPES, LAND, 100.0), 4.0)
