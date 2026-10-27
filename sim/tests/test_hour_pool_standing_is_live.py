"""The hour pool and priority rank a screen shows come from the live active list, not from the record written
when hours were last allocated (Complaint 640: the projects module over plain values)."""
QUICK_TOPIC = True

import types
import unittest

from .harness import *  # noqa: F401,F403
from sim.tests import projects_host
from sim.ui.proto import state_projects as proto_state
from sim.tests.ui_stand_in import Game
from sim.tests.ui_stand_in import FactViews


class _HourGame(FactViews):
    """Only what the hour queue and the active-project builder read: the module answers the standing."""
    goal = None
    bountied = frozenset()

    def __init__(self, node_ids, pool=120.0, committed=20.0, allocations=None):
        self.order = ["alpha", "beta", "gamma", "delta"]
        self.state = Game(
            projects=Game(active={node_id: self._stale_progress() for node_id in node_ids}),
            household=Game(hour_allocations=allocations or {}))
        self.module = projects_host.build(
            legacy_projects=self.state.projects, legacy_order=self.order, hour_commitments={"allocations": allocations or {}},
            hours_available={"director_pool": pool, "director_committed": committed})
        self.active = self.state.projects.active

    def hour_standing(self, node_id):
        return self.module.hour_standing(node_id)

    @staticmethod
    def _stale_progress():
        return {"ph_left": 10.0, "spent": 0.0, "yrs": 0, "pool_rank_this_year": 9,
                "pool_active_count_this_year": 9, "pool_total_this_year": 200.0}

    def project_cost(self, node_id):
        return 0.0

    def effective_risk(self, node_id):
        return 0.0


NODES_STUB = {name: {"name": name, "ph": 10, "risk": 0.0} for name in ("alpha", "beta", "gamma", "delta")}


class HourStandingIsLive(unittest.TestCase):

    def test_rank_and_count_follow_the_live_active_list(self):
        game = _HourGame(["gamma", "alpha", "beta"])
        self.assertEqual([game.view("hour_standing")(name)[:2] for name in ("alpha", "beta", "gamma")], [(1, 3), (2, 3), (3, 3)])

    def test_a_standing_allocation_moves_a_project_to_the_front(self):
        game = _HourGame(["alpha", "beta", "gamma"], allocations={"gamma": 40.0})
        self.assertEqual(game.view("hour_standing")("gamma")[0], 1)
        self.assertEqual(game.view("hour_standing")("alpha")[0], 2)

    def test_a_project_not_in_hand_has_no_standing(self):
        self.assertIsNone(_HourGame(["alpha"]).hour_standing("delta"))

    def test_pool_is_the_hours_not_yet_committed(self):
        game = _HourGame(["alpha", "beta"], pool=120.0, committed=20.0)
        self.assertAlmostEqual(game.view("hour_standing")("alpha")[2], 100.0)

    def test_pool_never_goes_below_zero(self):
        game = _HourGame(["alpha"], pool=10.0, committed=50.0)
        self.assertEqual(game.view("hour_standing")("alpha")[2], 0.0)

    def test_the_builder_reads_standing_not_the_stale_record(self):
        game = _HourGame(["beta", "alpha"], pool=120.0, committed=20.0)
        original = proto_state._waiting_on
        proto_state._waiting_on = lambda *arguments: ""
        try:
            rows = proto_state._agent_state_active_projects(game, NODES_STUB)
        finally:
            proto_state._waiting_on = original
        self.assertEqual((rows["alpha"]["pool_rank_this_year"], rows["beta"]["pool_rank_this_year"]), (1, 2))
        for row in rows.values():
            self.assertEqual(row["pool_active_count_this_year"], 2)
            self.assertAlmostEqual(row["pool_total_this_year"], 100.0)


if __name__ == "__main__":
    unittest.main()
