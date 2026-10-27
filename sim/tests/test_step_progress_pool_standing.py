"""The hour pool's standing is stored as the allocator uses it: `_step_progress` walks the queue in order handing each
project what the one before left, and `_step_progress_project` records the pool total, how many shared it, the
project's rank and what was left of the pool when its turn came. The offer itself is hour_offer (test_allocate)."""
QUICK_TOPIC = True

import types
import unittest

from sim.tests import module_harness, projects_host
from sim.workforce.api import ResetTradeHours


def _Phase(queue, take_per_project):
    """The projects module over a queue of projects each of which takes this many hours; one project's turn is a recorder."""
    module = projects_host.build(
        tree={node_id: {} for node_id in queue}, legacy_projects=types.SimpleNamespace(active={node_id: {} for node_id in queue}),
        revenue_estimate=0.0, upkeep=0.0, mine_operating_cost=0.0)
    module.turns = []
    module.unused_reported = None
    module.hour_priority_queue = lambda: list(queue)

    def report_unused_directed_hours(unused):
        module.unused_reported = unused

    def step_project(node_id, pool_rank, pool_total, active_count, remaining, hired_left, arrears_hours_lost, directed_hours_unused,
                     _afford_context=None):
        module.turns.append((node_id, pool_rank, pool_total, active_count, remaining))
        return remaining - take_per_project[node_id], hired_left, take_per_project[node_id] / 2.0
    module.report_unused_directed_hours = report_unused_directed_hours
    module._step_progress_project = step_project
    return module


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
        self.assertEqual([command for command in module_harness.sent(self.phase) if isinstance(command, ResetTradeHours)], [ResetTradeHours()])


def _Stage():
    """One project's first stage, halted at the trade gate."""
    module = projects_host.build(tree={"doctorate": {}}, legacy_projects=types.SimpleNamespace(active={"doctorate": {}}))
    module._project_progress_trade_gate = lambda node_id, project_state, node: True
    return module


class StandingStoredTests(unittest.TestCase):
    def test_the_standing_is_stored_on_the_project_before_anything_else_happens(self):
        stage = _Stage()
        stage._step_progress_project("doctorate", 2, 2000.0, 3, 1850.04, 7, [], [])
        stored = stage.needs.legacy_projects().active["doctorate"]
        self.assertEqual((stored["pool_total_this_year"], stored["pool_active_count_this_year"], stored["pool_rank_this_year"],
                          stored["pool_remaining_before_this_year"]), (2000.0, 3, 2, 1850.0))


if __name__ == "__main__":
    unittest.main()
