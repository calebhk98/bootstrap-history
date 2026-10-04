"""Complaints/40: technologies a recipe needs that no civilisation starts with.

The frontier is recipe gates held by nobody whose own prerequisites somebody
does hold. Each states `unheld_reason` in the tree data beside the node (the
validator reads it); no list lives in this test."""
import os
import unittest

from sim.engine import civ_start_check as start_check
from sim.engine import validate_unheld_gates
from sim.engine.catalog import load_production_catalog
from sim.engine.tree_source import load_base_tree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UnheldRecipeGateTests(unittest.TestCase):

    def setUp(self):
        self.nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        self.civilisations = start_check.load_civilisations(ROOT)
        self.production = load_production_catalog(ROOT)

    def test_every_frontier_gap_states_why_nobody_holds_it(self):
        self.assertEqual(
            validate_unheld_gates.check_unheld_gates(self.nodes, self.civilisations, self.production), [])

    def test_a_gap_needs_a_reason_and_a_held_gate_is_not_a_gap(self):
        gate = "gate"
        nodes = {"base": {"pre": []}, gate: {"pre": ["base"]}}
        production = {"widget": {"requires_node": gate}}
        civilisations = {"a": {"starting_techs": ["base"]}}
        self.assertEqual(len(validate_unheld_gates.check_unheld_gates(nodes, civilisations, production)), 1)
        nodes[gate]["unheld_reason"] = "no sourced start civilisation had this yet"
        self.assertEqual(validate_unheld_gates.check_unheld_gates(nodes, civilisations, production), [])
        civilisations["a"]["starting_techs"].append(gate)
        del nodes[gate]["unheld_reason"]
        self.assertEqual(validate_unheld_gates.check_unheld_gates(nodes, civilisations, production), [])


if __name__ == "__main__":
    unittest.main()
