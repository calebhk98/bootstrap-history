"""Scenario: the waiting line a screen shows for a project reads the live hour standing, not the record written
when hours were last allocated. The rules are in test_hour_pool_standing_is_live."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.ui.proto import state_projects as proto_state


def _household_with_projects(count):
    household = sim(civ="rome_100ad", capital=1e7)
    node_ids = [node_id for node_id in household.order
                if household.start_reason(node_id)[0] and NODES[node_id]["ph"] > 0][:count]
    for node_id in node_ids:
        household.start_project(node_id)
    return household, node_ids


def _stale_record(household):
    for progress in household.active.values():
        progress["pool_rank_this_year"] = 9
        progress["pool_active_count_this_year"] = 9
        progress["pool_total_this_year"] = 200.0


class HourStandingIsLive(unittest.TestCase):

    def test_rank_and_count_follow_the_live_active_list(self):
        household, node_ids = _household_with_projects(3)
        _stale_record(household)
        active = proto_state._agent_state_active_projects(household, household.nodes)
        ranks = sorted(active[node_id]["pool_rank_this_year"] for node_id in node_ids)
        self.assertEqual(ranks, [1, 2, 3])
        for node_id in node_ids:
            self.assertEqual(active[node_id]["pool_active_count_this_year"], 3)

    def test_waiting_line_does_not_quote_the_stale_pool(self):
        household, node_ids = _household_with_projects(2)
        _stale_record(household)
        active = proto_state._agent_state_active_projects(household, household.nodes)
        for node_id in node_ids:
            text = str(active[node_id]["waiting_on"])  # presentation: the waiting line is wording a player reads
            self.assertNotIn("#9", text)
            self.assertNotIn("of 9", text)
            self.assertNotIn("200 directed", text)
