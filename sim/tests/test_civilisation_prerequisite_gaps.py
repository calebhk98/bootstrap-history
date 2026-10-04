"""A civilisation holding a node without its prerequisites must declare it.

Complaints/41. The declaration lives in the civilisation's `prerequisite_gaps`
(node id -> reason); no list lives in this test."""
import os
import unittest

from sim.engine import civ_start_check as start_check
from sim.engine.catalog import load_production_catalog
from sim.engine.tree_source import load_base_tree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PrerequisiteGapTests(unittest.TestCase):

    def test_every_gap_in_the_real_data_is_declared(self):
        nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        for name, civilisation in start_check.load_civilisations(ROOT).items():
            errors, _warnings = start_check.prerequisite_gap_findings(
                name, civilisation, start_check.missing_prerequisites(nodes, civilisation))
            self.assertEqual(errors, [], name)

    def test_an_undeclared_gap_fails_and_an_unreviewed_one_warns(self):
        nodes = {"base": {"pre": []}, "top": {"pre": ["base"]}}
        civilisation = {"starting_techs": ["top"]}
        missing = start_check.missing_prerequisites(nodes, civilisation)
        errors, warnings = start_check.prerequisite_gap_findings("c", civilisation, missing)
        self.assertEqual((len(errors), len(warnings)), (1, 0))
        civilisation["prerequisite_gaps"] = {"top": "unreviewed"}
        errors, warnings = start_check.prerequisite_gap_findings("c", civilisation, missing)
        self.assertEqual((len(errors), len(warnings)), (0, 1))
        civilisation["prerequisite_gaps"] = {"top": "the history is clear and cited here"}
        self.assertEqual(start_check.prerequisite_gap_findings("c", civilisation, missing), ([], []))

    def test_a_held_prerequisite_needs_no_declaration(self):
        nodes = {"base": {"pre": []}, "top": {"pre": ["base"]}}
        civilisation = {"starting_techs": ["base", "top"]}
        self.assertEqual(start_check.missing_prerequisites(nodes, civilisation), {})


if __name__ == "__main__":
    unittest.main()
