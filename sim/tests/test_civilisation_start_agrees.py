"""A civilisation's starting state must agree with itself (Complaints/124).

sim/civ_start_check.py is the check; `simulator.py validate` prints it per
civilisation. Here: a deliberately broken fixture proves each class is caught,
and the shipped civilisations must have no free-but-unheld node.
"""
import os
import unittest

from sim import civ_start_check as start_check
from sim.engine.tree_source import load_base_tree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _node(node_id, pre=(), cap=0.0, mat=None, req_any=None):
    return {"id": node_id, "pre": list(pre), "cap_hours": cap, "ph": 0.0, "yrs": 0.0,
            "lab": {}, "mat": mat or {}, "req_any": req_any or []}


FIXTURE_NODES = {
    "known_idea": _node("known_idea"),
    "free_child": _node("free_child", pre=["known_idea"]),
    "priced": _node("priced", cap=100.0),
    "needs_priced": _node("needs_priced", pre=["priced"]),
    "gated_free": _node("gated_free"),
    "gate": _node("gate", cap=5.0),
    "uses_steel": _node("uses_steel", cap=1.0, mat={"steel_kg": 1.0}),
}
FIXTURE_PRODUCTION = {"steel_kg": {"outputs": {"steel_kg": 1.0}, "requires_node": "priced"}}


class StartAgreesWithItselfTests(unittest.TestCase):

    def test_free_node_not_held_is_reported_with_its_free_descendants(self):
        civ = {"starting_techs": []}
        self.assertEqual(start_check.free_unheld(FIXTURE_NODES, civ),
                         ["free_child", "gated_free", "known_idea"])

    def test_holding_the_free_node_clears_it(self):
        civ = {"starting_techs": ["known_idea", "free_child", "gated_free"]}
        self.assertEqual(start_check.free_unheld(FIXTURE_NODES, civ), [])

    def test_needs_first_gate_refuses_a_free_node(self):
        civ = {"starting_techs": ["known_idea", "free_child"],
               "needs_first": {"import": {"node": "gate", "ids": ["gated_free"]}}}
        self.assertEqual(start_check.free_unheld(FIXTURE_NODES, civ), [])

    def test_held_node_without_prerequisite_is_reported(self):
        civ = {"starting_techs": ["needs_priced"]}
        self.assertEqual(start_check.missing_prerequisites(FIXTURE_NODES, civ),
                         {"needs_priced": ["priced"]})

    def test_material_no_available_recipe_makes_is_reported(self):
        civ = {"starting_techs": ["uses_steel"]}
        self.assertEqual(
            start_check.unmakeable_materials(FIXTURE_NODES, civ, FIXTURE_PRODUCTION),
            {"uses_steel": ["steel_kg"]})
        civ = {"starting_techs": ["uses_steel", "priced"]}
        self.assertEqual(
            start_check.unmakeable_materials(FIXTURE_NODES, civ, FIXTURE_PRODUCTION), {})

    def test_held_capability_rung_without_the_rung_below_is_reported(self):
        nodes = {"rung_low": _node("rung_low"),
                 "rung_high": _node("rung_high", pre=["rung_low"]),
                 "tool": _node("tool", pre=["rung_high"])}
        for node in nodes.values():
            node["cat"] = "capability" if node["id"].startswith("rung") else "tool"
        civ = {"starting_techs": ["rung_high", "tool"]}
        self.assertEqual(start_check.capability_rung_gaps(nodes, civ),
                         {"rung_high": ["rung_low"], "tool": ["rung_low"]})
        civ = {"starting_techs": ["rung_low", "rung_high", "tool"]}
        self.assertEqual(start_check.capability_rung_gaps(nodes, civ), {})

    def test_held_node_the_briefing_says_is_absent_is_reported(self):
        civ = {"starting_techs": ["known_idea"],
               "briefing_absent": [{"claim": "no ideas here", "nodes": ["known_idea", "priced"]}]}
        self.assertEqual(start_check.briefing_contradictions(FIXTURE_NODES, civ),
                         {"no ideas here": ["known_idea"]})
        civ["starting_techs"] = []
        self.assertEqual(start_check.briefing_contradictions(FIXTURE_NODES, civ), {})

    def test_shipped_civilisations_hold_nothing_their_briefing_says_is_absent(self):
        nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        for name, civilisation in start_check.load_civilisations(ROOT).items():
            self.assertEqual(start_check.briefing_contradictions(nodes, civilisation), {}, name)

    def test_shipped_civilisations_have_no_free_but_unheld_node(self):
        nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        for name, civilisation in start_check.load_civilisations(ROOT).items():
            self.assertEqual(start_check.free_unheld(nodes, civilisation), [],
                             "%s can start these for free at arrival without holding them"
                             % name)

    def test_no_shipped_civilisation_holds_a_node_whose_capability_rung_it_lacks(self):
        nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        for name, civilisation in start_check.load_civilisations(ROOT).items():
            self.assertEqual(start_check.capability_rung_gaps(nodes, civilisation), {},
                             "%s holds these without the capability rung they need" % name)


if __name__ == "__main__":
    unittest.main()
