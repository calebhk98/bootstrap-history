"""Complaint 640: committed_spend is the sum of what every project in hand still owes; the director's yearly start phase
starts a candidate only when its cost fits funding_capacity() less committed_spend(); the leverage list's stacking
caution is given once. The judging rule is in test_auto_start_rule and the funding parts in test_affordability_warning."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import step_phase_project_start
from sim.engine.economy_credit import CreditMixin
from sim.engine.step_phase_project_start import ProjectStartPhaseMixin
from sim.ui.proto.techtree import _digest_stack_caution


class Projects:
    def __init__(self, active):
        self.active = active
        self.bountied = set()
        self.done = set()

    def active_keys_sorted(self):
        return sorted(self.active)


class Purse(CreditMixin):
    def __init__(self, active):
        self.state = types.SimpleNamespace(projects=Projects(active))


class CommittedSpend(unittest.TestCase):
    def test_it_sums_what_each_project_in_hand_still_owes_and_counts_a_missing_figure_as_nothing(self):
        purse = Purse({"b": {"cost_left": 30.0}, "a": {"cost_left": 12.5}, "c": {"cost_left": None}, "d": {}})
        self.assertEqual(purse.committed_spend(), 42.5)

    def test_no_work_in_hand_commits_nothing(self):
        self.assertEqual(Purse({}).committed_spend(), 0.0)


class Director(ProjectStartPhaseMixin):
    MAX_ACTIVE_PROJECTS_BASE = 5.0
    MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS = 2000.0
    MAX_ACTIVE_PROJECTS_PER_SCHOLAR = 12.0
    MAX_ACTIVE_PROJECTS_PER_ARTISAN = 40.0

    def __init__(self, funding_capacity, committed_spend, project_cost=9000.0):
        self.manual = False
        self.state = types.SimpleNamespace(
            scenario=types.SimpleNamespace(year=0),
            household=types.SimpleNamespace(credit_frozen_until=0, scholars=0.0, artisans=0.0, capital=1e7),
            projects=Projects({}))
        self.labour = types.SimpleNamespace(director_pool=lambda: 0.0, director_hours_committed=lambda: 0.0,
                                            hired_cap=lambda: 0.0)
        self.nodes = {"a": {"name": "a", "rev": 0.0, "up": 0.0}, "b": {"name": "b", "rev": 0.0, "up": 0.0}}
        self.order = ["a", "b"]
        self.bounty_set = set()
        self.audit = []
        self._funding = funding_capacity
        self._committed = committed_spend
        self._cost = project_cost
        self.started = []

    def upkeep(self):
        return 0.0

    def revenue(self):
        return 1e6

    def living_cost(self, _rev=None, _upkeep=None):
        return 0.0

    def mine_operating_cost(self):
        return 0.0

    def can_start(self, node_id):
        return True

    def project_cost(self, node_id):
        return self._cost

    def funding_capacity(self):
        return self._funding

    def committed_spend(self):
        return self._committed

    def initialize_project(self, node_id):
        self.started.append(node_id)
        self.state.projects.active[node_id] = {}


class StartPhase(unittest.TestCase):
    def _started(self, funding_capacity, committed_spend):
        director = Director(funding_capacity, committed_spend)
        with mock.patch.object(step_phase_project_start, "automation_audit"):
            director._step_start_projects()
        return director.started

    def test_room_that_clears_the_cost_starts_work(self):
        self.assertTrue(self._started(funding_capacity=1e5, committed_spend=0.0))

    def test_a_capacity_just_below_the_cost_starts_nothing(self):
        self.assertEqual(self._started(funding_capacity=8000.0, committed_spend=0.0), [])

    def test_a_huge_capacity_eaten_by_what_is_committed_starts_nothing(self):
        self.assertEqual(self._started(funding_capacity=1e7, committed_spend=1e7 - 5000.0), [])

    def test_a_manual_game_starts_nothing(self):
        director = Director(1e9, 0.0)
        director.manual = True
        director._step_start_projects()
        self.assertEqual(director.started, [])


class StackCaution(unittest.TestCase):
    def test_it_is_given_the_first_time_a_leverage_list_is_shown_and_never_again(self):
        game = types.SimpleNamespace()
        first = _digest_stack_caution(game, ["some_node"])
        self.assertTrue(first)
        self.assertIsNone(_digest_stack_caution(game, ["some_node"]))

    def test_an_empty_leverage_list_gives_none_and_does_not_use_up_the_caution(self):
        game = types.SimpleNamespace()
        self.assertIsNone(_digest_stack_caution(game, []))
        self.assertTrue(_digest_stack_caution(game, ["some_node"]))


if __name__ == "__main__":
    unittest.main()
