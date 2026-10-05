"""Complaint 116: relationships between two systems that neither system's own tests see. Each test states
one invariant over a range of inputs on a game that does not need the agent economy, so the file is fast.
To add one, build `_fresh_sim()`, drive the two systems and assert the relationship (see the list in 116)."""
import math
import random
import unittest

from sim.engine import data
from sim.engine.projects_completion import goal_movement
from sim.engine.ui_port import Sim, load, load_civ

_TREE, _PRICES, _NODES, _WAGES, _GOODS = load()
LITERACY_GOAL = "goal_literacy_common"


def _fresh_sim(goal=None):
    sim = Sim(_NODES, [], random.Random(1), events=False, manual=True, civ=load_civ("rome_100ad"))
    sim.done_year = {}
    if goal:
        sim.goal = goal
    return sim


class EventLossInvariants(unittest.TestCase):
    def test_a_mortality_shock_never_removes_more_people_than_exist(self):
        for raw in (0.05, 0.45, 0.99, 3.0):
            sim = _fresh_sim()
            before = sim.population.total
            sim._apply_population_mortality_shock(raw)
            population = sim.population
            for cohort in (population.children, population.working_age, population.elderly):
                self.assertGreaterEqual(cohort, 0.0, raw)
            self.assertLessEqual(before - population.total, before + 1e-9, raw)
            self.assertLessEqual(population.total, before + 1e-9, raw)

    def test_a_small_shock_removes_the_share_it_names(self):
        sim = _fresh_sim()
        before = sim.population.total
        sim._apply_population_mortality_shock(0.2)
        self.assertAlmostEqual((before - sim.population.total) / before, 0.2, places=6)

    def test_staff_survival_never_adds_people(self):
        for share in (0.0, 0.3, 0.9, 1.0):
            sim = _fresh_sim()
            household = sim.state.household
            before = household.scholars + household.artisans + sum(household.employees.values())
            sim.apply_staff_survival(share)
            after = household.scholars + household.artisans + sum(household.employees.values())
            self.assertLessEqual(after, before + 1e-9, share)
            self.assertTrue(all(count > 0 for count in household.employees.values()))


class CeilingInvariants(unittest.TestCase):
    def test_a_technology_never_pushes_literacy_past_its_ceiling(self):
        for field, ceiling_of in (("literacy_general", "literacy_ceiling_general"),
                                  ("literacy_elite", "literacy_ceiling_elite")):
            sim = _fresh_sim()
            start = float(sim.civ.get(field, 0.0))
            sim_node = LITERACY_GOAL
            saved = data.TECH_EFFECTS.get(sim_node)
            data.TECH_EFFECTS[sim_node] = {field: 5.0}
            try:
                sim.apply_tech_effects(sim_node)
            finally:
                data.TECH_EFFECTS.pop(sim_node)
                if saved is not None:
                    data.TECH_EFFECTS[sim_node] = saved
            ceiling = getattr(sim, ceiling_of)()
            self.assertLessEqual(sim.civ[field], max(ceiling, start) + 1e-9, field)

    def test_the_ceilings_are_fractions(self):
        sim = _fresh_sim()
        for ceiling in (sim.literacy_ceiling_general(), sim.literacy_ceiling_elite()):
            self.assertTrue(0.0 < ceiling <= 1.0)
        self.assertLessEqual(sim.literacy_ceiling_general(), sim.literacy_ceiling_elite() + 1e-9)


class GoalDeltaInvariants(unittest.TestCase):
    def test_the_reported_goal_delta_is_the_change_in_the_live_measure(self):
        sim = _fresh_sim(LITERACY_GOAL)
        before = sim.goal_snapshot()
        sim.civ["literacy_general"] = sim.civ.get("literacy_general", 0.0) + 0.03
        after = sim.goal_snapshot()
        moved, _gained = goal_movement(before, after)
        labels = {label: (old, new) for label, old, new in moved}
        self.assertIn("literacy general", labels)
        live = sim.civ["literacy_general"]
        self.assertAlmostEqual(after["measures"]["literacy general"][0], live)
        self.assertAlmostEqual(live - before["measures"]["literacy general"][0], 0.03)
        for label, (old_value, _fraction) in before["measures"].items():
            new_value = after["measures"][label][0]
            self.assertEqual(label in labels, abs(new_value - old_value) > 1e-9, label)

    def test_nothing_is_reported_when_nothing_moved(self):
        sim = _fresh_sim(LITERACY_GOAL)
        snapshot = sim.goal_snapshot()
        moved, gained = goal_movement(snapshot, sim.goal_snapshot())
        self.assertEqual((moved, gained), ([], 0))
        self.assertTrue(all(math.isfinite(value) for value, _fraction in snapshot["measures"].values()))


if __name__ == "__main__":
    unittest.main()
