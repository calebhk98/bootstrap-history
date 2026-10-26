"""Complaint 640: committed_spend is the sum of what every project in hand still owes; the director's yearly start phase
starts a candidate only when its cost fits funding_capacity() less committed_spend(); the leverage list's stacking
caution is given once. The judging rule is in test_auto_start_rule and the funding parts in test_affordability_warning."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.economy_credit import CreditMixin
from sim.tests import projects_host
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


def director(funding_capacity, committed_spend, project_cost=9000.0, manual=False):
    """The projects module, its start phase ready to run: every candidate can start, and the room is what is given."""
    state = projects_host.projects_state()
    module = projects_host.build(
        legacy_projects=state, tree=lambda node_id: {"name": node_id, "rev": 0.0, "up": 0.0}, legacy_order=["a", "b"],
        funding_capacity=funding_capacity, committed_cost=committed_spend, project_cost=lambda node_id: project_cost,
        automation={"manual": manual, "bounty_set": set()}, revenue_estimate=1e6, acting_balance=1e7, year=0,
        start_check=lambda *arguments: (True, None),
        project_limits={"base": 5.0, "per_director_hours": 2000.0, "per_scholar": 12.0, "per_artisan": 40.0})
    module.started = []

    def initialize_project(node_id):
        module.started.append(node_id)
        state.active[node_id] = {}
    module.initialize_project = initialize_project
    return module


class StartPhase(unittest.TestCase):
    def _started(self, funding_capacity, committed_spend):
        module = director(funding_capacity, committed_spend)
        module.start_projects_phase("founder")
        return module.started

    def test_room_that_clears_the_cost_starts_work(self):
        self.assertTrue(self._started(funding_capacity=1e5, committed_spend=0.0))

    def test_a_capacity_just_below_the_cost_starts_nothing(self):
        self.assertEqual(self._started(funding_capacity=8000.0, committed_spend=0.0), [])

    def test_a_huge_capacity_eaten_by_what_is_committed_starts_nothing(self):
        self.assertEqual(self._started(funding_capacity=1e7, committed_spend=1e7 - 5000.0), [])

    def test_a_manual_game_starts_nothing(self):
        module = director(1e9, 0.0, manual=True)
        module.start_projects_phase("founder")
        self.assertEqual(module.started, [])


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
