"""Complaint 133: one "held and running" answer, and the results an action returns (knowledge, route, partner).

Small fixtures only; nothing here builds a game."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine import validate_action_results
from sim.land import action_results
from sim.land.map_views import GeographyInputs
from sim.land.module import Land
from sim.land.state import LandSeat, LandWorld
from sim.tests import module_harness
from sim.workforce.world import WorkforceWorld

NODES = {
    "harbour": {"id": "harbour", "up": 5.0, "rev": 0.0},
    "voyage": {"id": "voyage", "up": 0.0, "rev": 0.0,
               "returns": {"route": ["far_sea"], "knowledge": ["star_chart"], "partner": ["distant_realm"]}},
    "star_chart": {"id": "star_chart", "up": 0.0, "rev": 0.0},
    "lore": {"id": "lore", "up": 0.0, "rev": 0.0},
    "wharf": {"id": "wharf", "up": 3.0, "rev": 0.0, "returns": {"route": ["river_mouth"]}},
}


class _Host:
    """The land module over plain values for the views the held answer reads."""

    def __init__(self, done, operating, granted=(), starting=("lore",)):
        self.done, self.operating, self.granted = set(done), set(operating), set(granted)
        self.versions = [1, 1]
        self.module = module_harness.build(
            Land, world=LandWorld(), seat=LandSeat(),
            views={"legacy_done_versions": lambda: tuple(self.versions), "tree_nodes": NODES,
                   "techniques_held": lambda: self.done, "techniques_granted": lambda: self.granted,
                   "running": self.running, "civilisation": {"starting_techs": list(starting)}})

    def running(self, node_id):
        node = NODES[node_id]
        if node_id not in self.done:
            return False
        return node_id in self.operating if (node["up"] or node["rev"]) else True

    def held_and_running(self, include_starting=True):
        return self.module.held_techniques(include_starting)

    def partner_gate_refusal(self, civilization_id):
        return self.module.partner_gate_refusal(civilization_id)


class ResultTokenTests(unittest.TestCase):

    def test_a_result_is_named_by_its_kind_except_knowledge_which_is_the_node_itself(self):
        self.assertEqual(action_results.token("route", "far_sea"), "route:far_sea")
        self.assertEqual(action_results.token("partner", "distant_realm"), "partner:distant_realm")
        self.assertEqual(action_results.token("knowledge", "star_chart"), "star_chart")

    def test_a_held_action_returns_every_kind_it_declares(self):
        self.assertEqual(action_results.results_of(NODES, {"voyage"}),
                         {"route:far_sea", "partner:distant_realm", "star_chart"})

    def test_a_node_without_results_returns_nothing(self):
        self.assertEqual(action_results.results_of(NODES, {"lore", "unknown"}), set())

    def test_the_tokens_asked_for_by_a_lane_are_those_an_action_can_return(self):
        problems = validate_action_results.check_action_results(
            NODES, [{"id": "lane", "requires_nodes": ["route:far_sea", "route:nowhere", "voyage"]}])
        self.assertEqual(len(problems), 1)
        self.assertIn("route:nowhere", problems[0])

    def test_a_result_of_an_unknown_kind_or_naming_nothing_is_refused(self):
        nodes = {"a": {"id": "a", "returns": {"gold": ["x"]}},
                 "b": {"id": "b", "returns": {"knowledge": ["missing_node"]}}}
        problems = validate_action_results.check_action_results(nodes, [])
        self.assertEqual(len(problems), 2)


class HeldAndRunningTests(unittest.TestCase):

    def test_starting_done_and_granted_nodes_are_held(self):
        host = _Host(done={"lore", "star_chart"}, operating=(), granted={"star_chart"})
        self.assertEqual(host.held_and_running(), {"lore", "star_chart"})

    def test_a_venture_that_is_shut_is_not_held(self):
        shut = _Host(done={"harbour"}, operating=())
        self.assertNotIn("harbour", shut.held_and_running())
        self.assertIn("harbour", _Host(done={"harbour"}, operating={"harbour"}).held_and_running())

    def test_the_starting_techs_can_be_left_out(self):
        host = _Host(done={"star_chart"}, operating=())
        self.assertEqual(host.held_and_running(include_starting=False), {"star_chart"})

    def test_results_stand_while_the_action_is_held_and_running(self):
        open_wharf = _Host(done={"wharf"}, operating={"wharf"})
        self.assertIn("route:river_mouth", open_wharf.held_and_running())
        closed_wharf = _Host(done={"wharf"}, operating=())
        self.assertNotIn("route:river_mouth", closed_wharf.held_and_running())

    def test_a_voyage_returns_its_route_knowledge_and_partner(self):
        held = _Host(done={"voyage"}, operating=()).held_and_running()
        self.assertTrue({"route:far_sea", "partner:distant_realm", "star_chart"} <= held)

    def test_a_node_the_tree_does_not_know_stays_held(self):
        host = _Host(done={"modded_away"}, operating=())
        self.assertIn("modded_away", host.held_and_running())

    def test_the_answer_follows_a_change_in_what_is_open(self):
        host = _Host(done={"harbour"}, operating=())
        self.assertNotIn("harbour", host.held_and_running())
        host.operating.add("harbour")
        host.versions[1] += 1
        self.assertIn("harbour", host.held_and_running())


class AuthoredDataTests(unittest.TestCase):

    def test_every_route_a_lane_asks_for_is_returned_by_an_authored_expedition(self):
        from sim.engine import tree_merge
        from sim.geography.api import open_map
        nodes = {node["id"]: node for node in tree_merge.build_tree().tree["nodes"]}
        world_map = open_map()
        entries = list(world_map.catalogue("route_modes").values()) + list(world_map.catalogue("sea_lanes").values())
        self.assertEqual(validate_action_results.check_action_results(nodes, entries), [])
        asked = {needed for entry in entries for needed in entry.get("requires_nodes") or () if needed.startswith("route:")}
        self.assertTrue(asked)
        self.assertEqual(asked - action_results.results_of(nodes, nodes), set())


class CallersTests(unittest.TestCase):

    def test_geography_reads_the_one_answer(self):
        module = SimpleNamespace(needs=SimpleNamespace(held_techniques=lambda include_starting: {"a", "b"} if include_starting else {"b"}))
        self.assertEqual(GeographyInputs(module).held_nodes, {"a", "b"})

    def test_labour_reads_the_one_answer(self):
        needs = SimpleNamespace(held_techniques=lambda include_starting: frozenset({"a"}))
        self.assertEqual(WorkforceWorld(needs, None).held_and_running(), frozenset({"a"}))

    def test_a_partner_an_action_returns_is_refused_until_it_is_held(self):
        host = _Host(done=set(), operating=())
        self.assertIn("distant_realm", host.partner_gate_refusal("distant_realm") or "")
        host.done.add("voyage")
        host.versions[0] += 1
        self.assertIsNone(host.partner_gate_refusal("distant_realm"))
        self.assertIsNone(host.partner_gate_refusal("never_returned_by_anything"))


if __name__ == "__main__":
    unittest.main()
