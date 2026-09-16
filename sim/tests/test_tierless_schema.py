"""Focused regression tests for the staged removal of technology tiers."""
import copy
import json
import os
import tempfile
import unittest
from unittest import mock

from sim import treetool
from sim.engine import data


MIGRATED_BRANCHES = (
    "40_finance_institutions.json",
    "41_chemistry_deep.json",
    "42_electrical_deep.json",
    "43_manufacturing_deep.json",
    "44_medicine_deep.json",
    "45a_transport_land_deep.json",
    "45b_transport_rail_marine_deep.json",
)


class TierlessSchemaTests(unittest.TestCase):
    def test_migrated_branch_nodes_are_tierless(self):
        for filename in MIGRATED_BRANCHES:
            with self.subTest(filename=filename):
                path = os.path.join(treetool.BR, filename)
                with open(path) as source:
                    nodes = json.load(source)
                self.assertTrue(nodes)
                self.assertFalse([node["id"] for node in nodes if "tier" in node])

    def test_treetool_accepts_and_normalises_a_tierless_node(self):
        node = {
            "id": "test_tierless",
            "name": "Tierless test node",
            "cat": "test",
            "pre": [],
            "note": "Exercises the transitional schema.",
        }

        self.assertFalse(set(treetool.REQUIRED) - set(node))
        normalised = treetool.normalise_v2(copy.deepcopy(node))
        self.assertEqual(normalised["tier"], 2)

    def test_runtime_loads_a_tierless_node(self):
        with open(data.TREE) as source:
            tree = json.load(source)
        node = copy.deepcopy(tree["nodes"][0])
        node.pop("tier", None)
        tree["nodes"] = [node]

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(tree, f)
            path = f.name
        try:
            with mock.patch.object(data, "TREE", path):
                _, _, nodes, _, _ = data.load()
            self.assertEqual(nodes[node["id"]]["tier"], 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
