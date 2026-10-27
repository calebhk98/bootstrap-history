"""The hour pool's standing is stored as the allocator uses it: `_step_progress` walks the queue in order handing each
project what the one before left, and `_step_progress_project` records the pool total, how many shared it, the
project's rank and what was left of the pool when its turn came. The offer itself is hour_offer (test_allocate)."""
QUICK_TOPIC = True

import types
import unittest

from sim.workforce.api import ResetTradeHours
from sim.engine.step_phase_projects import ProjectProgressPhaseMixin


class _Phase(ProjectProgressPhaseMixin):
    """The parts of a Sim that the project loop and one project's first stage touch."""

    def __init__(self, queue, take_per_project):
        self.queue = queue
        self.take = take_per_project
        self.turns = []
        self.unused_reported = None
        self.state = types.SimpleNamespace(projects=types.SimpleNamespace(active={node_id: {} for node_id in queue}))
        self.reset = []
        self.nodes = {node_id: {} for node_id in queue}

    def send(self, command):
        self.reset.append(command)

    def hour_priority_queue(self):
        return list(self.queue)

    def revenue(self):
        return 0.0

    def upkeep(self):
        return 0.0

    def mine_operating_cost(self):
        return 0.0

    def report_unused_directed_hours(self, unused):
        self.unused_reported = unused

    def _step_progress_project(self, node_id, pool_rank, pool_total, active_count, remaining, hired_left,
                               arrears_hours_lost, directed_hours_unused, _afford_context=None):
        self.turns.append((node_id, pool_rank, pool_total, active_count, remaining))
        return remaining - self.take[node_id], hired_left, self.take[node_id] / 2.0


class QueueWalkTests(unittest.TestCase):
    def setUp(self):
        self.phase = _Phase(["doctorate", "curriculum", "library"], {"doctorate": 150.0, "curriculum": 120.0, "library": 30.0})
        self.result = self.phase._step_progress(2000.0, 5)

    def test_projects_are_taken_in_queue_order_with_ranks_from_one(self):
        self.assertEqual([(node_id, rank) for node_id, rank, _t, _c, _r in self.phase.turns],
                         [("doctorate", 1), ("curriculum", 2), ("library", 3)])

    def test_every_project_is_told_the_whole_pool_and_the_number_sharing_it(self):
        self.assertEqual({(total, count) for _n, _k, total, count, _r in self.phase.turns}, {(2000.0, 3)})

    def test_each_project_sees_what_the_ones_before_it_left(self):
        self.assertEqual([remaining for *_rest, remaining in self.phase.turns], [2000.0, 1850.0, 1730.0])

    def test_the_pool_left_and_the_hours_that_did_work_are_returned(self):
        remaining, remaining_after_projects, effective = self.result
        self.assertEqual((remaining, remaining_after_projects, effective), (1700.0, 1700.0, 150.0))

    def test_the_trade_hours_used_start_afresh_each_year(self):
        self.assertEqual(self.phase.reset, [ResetTradeHours()])


class _Stage(ProjectProgressPhaseMixin):
    """One project's first stage, halted at the trade gate."""

    def __init__(self):
        self.state = types.SimpleNamespace(projects=types.SimpleNamespace(active={"doctorate": {}}))
        self.nodes = {"doctorate": {}}

    def _project_progress_trade_gate(self, node_id, project_state, node):
        return True


class StandingStoredTests(unittest.TestCase):
    def test_the_standing_is_stored_on_the_project_before_anything_else_happens(self):
        stage = _Stage()
        stage._step_progress_project("doctorate", 2, 2000.0, 3, 1850.04, 7, [], [])
        stored = stage.state.projects.active["doctorate"]
        self.assertEqual((stored["pool_total_this_year"], stored["pool_active_count_this_year"], stored["pool_rank_this_year"],
                          stored["pool_remaining_before_this_year"]), (2000.0, 3, 2, 1850.0))


if __name__ == "__main__":
    unittest.main()
