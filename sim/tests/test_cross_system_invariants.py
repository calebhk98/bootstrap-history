"""Complaint 116: relationships between two systems that neither system's own tests see. Each invariant is stated over
a range of inputs on the rule itself, called with figures built here (a population, a household, a ceiling); one named
scenario reads the live goal measure through a game."""
QUICK_TOPIC = True

import math
import random
import unittest
from types import SimpleNamespace

from sim.diffusion.literacy_rules import literacy_after_effect as target_after_effect
from sim.diffusion.literacy_rules import common_ceiling
from sim.demography.api import rules as demography_rules
from sim.engine.projects_completion import goal_movement
from sim.tests import module_harness
from sim.workforce.api import SurviveStaff
from sim.workforce.module import Workforce

CHILD, WORKING_AGE, ELDERLY = 1.6, 1.0, 1.4   # the vulnerability ratios (sim/world/demography.py)


class Cohorts:
    def __init__(self, children=300.0, working_age=600.0, elderly=100.0):
        self.children, self.working_age, self.elderly = children, working_age, elderly

    @property
    def total(self):
        return self.children + self.working_age + self.elderly


def shocked(raw, **cohorts):
    population = Cohorts(**cohorts)
    before = population.total
    demography_rules.cut_cohorts(population, raw, CHILD, WORKING_AGE, ELDERLY)
    return population, before


class EventLossInvariants(unittest.TestCase):
    def test_a_mortality_shock_never_removes_more_people_than_exist(self):
        for raw in (0.05, 0.45, 0.99, 3.0):
            population, before = shocked(raw)
            for cohort in (population.children, population.working_age, population.elderly):
                self.assertGreaterEqual(cohort, 0.0, raw)
            self.assertLessEqual(before - population.total, before + 1e-9, raw)
            self.assertLessEqual(population.total, before + 1e-9, raw)

    def test_a_small_shock_removes_the_share_it_names(self):
        population, before = shocked(0.2)
        self.assertAlmostEqual((before - population.total) / before, 0.2, places=6)

    def test_the_young_and_the_old_lose_a_larger_share_than_working_age(self):
        population, _before = shocked(0.2)
        self.assertLess(population.children / 300.0, population.working_age / 600.0)
        self.assertLess(population.elderly / 100.0, population.working_age / 600.0)

    def test_no_shock_or_an_empty_population_changes_nothing(self):
        population, before = shocked(0.0)
        self.assertEqual(population.total, before)
        empty, _ = shocked(0.5, children=0.0, working_age=0.0, elderly=0.0)
        self.assertEqual(empty.total, 0.0)

    def test_staff_survival_never_adds_people(self):
        for share in (0.0, 0.3, 0.9, 1.0):
            household = SimpleNamespace(scholars=40.0, artisans=60.0, employees={"smith": 25.0, "miller": 3.0})
            workforce = module_harness.build(Workforce, seat=household, views={"legacy_acting_household": household, "legacy_dice": random.Random(1)})
            before = household.scholars + household.artisans + sum(household.employees.values())
            workforce.survive_staff(SurviveStaff(share))
            after = household.scholars + household.artisans + sum(household.employees.values())
            self.assertLessEqual(after, before + 1e-9, share)
            self.assertTrue(all(count > 0 for count in household.employees.values()))

    def test_a_survival_share_of_one_keeps_everyone_and_zero_keeps_no_one(self):
        for share, kept in ((1.0, 128.0), (0.0, 0.0)):
            household = SimpleNamespace(scholars=40.0, artisans=60.0, employees={"smith": 25.0, "miller": 3.0})
            workforce = module_harness.build(Workforce, seat=household, views={"legacy_acting_household": household, "legacy_dice": random.Random(1)})
            workforce.survive_staff(SurviveStaff(share))
            self.assertEqual(household.scholars + household.artisans + sum(household.employees.values()), kept)


class CeilingInvariants(unittest.TestCase):
    def test_a_technology_never_pushes_literacy_past_its_ceiling(self):
        for before in (0.0, 0.2, 0.6):
            self.assertLessEqual(target_after_effect(before, 5.0, 0.9), 0.9)

    def test_a_field_already_past_its_ceiling_is_not_pulled_down(self):
        self.assertEqual(target_after_effect(0.95, 0.1, 0.9), 0.95)

    def test_a_negative_effect_never_takes_literacy_below_nothing(self):
        self.assertEqual(target_after_effect(0.1, -5.0, 0.9), 0.0)

    def test_the_common_ceiling_is_a_fraction_and_falls_as_farm_hours_rise(self):
        previous = None
        for farm_share in (0.0, 0.3, 0.6, 0.9):
            ceiling = common_ceiling(0.01, 0.8, farm_share)
            self.assertTrue(0.0 < ceiling <= 1.0, farm_share)
            if previous is not None:
                self.assertLess(ceiling, previous)
            previous = ceiling

    def test_the_common_ceiling_never_exceeds_the_elite_ceiling(self):
        self.assertLessEqual(common_ceiling(0.01, 0.8, 0.0), 1.0 - 0.01 + 1e-12)


class GoalDeltaInvariants(unittest.TestCase):
    def test_nothing_is_reported_when_nothing_moved(self):
        snapshot = {"measures": {"literacy general": (0.2, True)}, "road_done": 2}
        self.assertEqual(goal_movement(snapshot, dict(snapshot)), ([], 0))
        self.assertTrue(all(math.isfinite(value) for value, _fraction in snapshot["measures"].values()))

    def test_only_the_measures_that_moved_are_reported_and_the_road_steps_gained_are_counted(self):
        before = {"measures": {"literacy general": (0.2, True), "ceiling": (0.5, True)}, "road_done": 2}
        after = {"measures": {"literacy general": (0.23, True), "ceiling": (0.5, True)}, "road_done": 5}
        moved, gained = goal_movement(before, after)
        self.assertEqual([label for label, _old, _new in moved], ["literacy general"])
        self.assertEqual(gained, 3)


if __name__ == "__main__":
    unittest.main()
