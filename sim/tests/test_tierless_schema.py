"""Focused regression tests for the tierless technology schema.

unittest-style; each TestCase method is reported as one check.
"""
import copy
import glob
import json
import os
import tempfile
import unittest
from unittest import mock

from sim import treetool
from sim import build_index
from sim.engine import data
from sim.engine.tree_source import load_base_tree


def branch_files():
    return sorted(glob.glob(os.path.join(treetool.BR, "[0-9]*.json")))


def review_snapshots():
    return sorted(glob.glob(os.path.join(data.ROOT, "data", "review", "*.json")))


def node_lists(paths):
    """Each JSON file that is a list of node records, as (path, records)."""
    for path in paths:
        with open(path) as source:
            records = json.load(source)
        if isinstance(records, list) and records and all(isinstance(r, dict) for r in records):
            yield path, records


class TierlessSchemaTests(unittest.TestCase):
    def test_generated_index_does_not_render_tiers(self):
        readme = os.path.join(build_index.KB, "README.md")
        with open(readme) as source:
            text = source.read()
        self.assertNotIn("| Node | Tier |", text)
        self.assertNotIn("| Node | Tier | Your hours | Documented in |", text)

    def test_branch_nodes_are_tierless(self):
        found = list(node_lists(branch_files()))
        self.assertTrue(found)
        for path, nodes in found:
            with self.subTest(filename=os.path.basename(path)):
                self.assertFalse([node["id"] for node in nodes if "tier" in node])

    def test_generated_tree_matches_tierless_sources(self):
        source_ids = set()
        for _path, nodes in node_lists(branch_files()):
            source_ids.update(node["id"] for node in nodes)
        generated_nodes = load_base_tree()["nodes"]
        tiered_ids = {node["id"] for node in generated_nodes if "tier" in node}
        self.assertFalse(source_ids & tiered_ids)

    def test_review_snapshots_are_tierless(self):
        for path, nodes in node_lists(review_snapshots()):
            with self.subTest(filename=os.path.basename(path)):
                self.assertFalse([node.get("id") for node in nodes if "tier" in node])

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
        self.assertNotIn("tier", normalised)

    def test_runtime_loads_a_tierless_node(self):
        tree = load_base_tree()
        node = copy.deepcopy(tree["nodes"][0])
        node.pop("tier", None)
        tree["nodes"] = [node]

        with mock.patch.object(data, "load_base_tree", return_value=tree):
            _, _, nodes, _, _ = data.load()
        self.assertNotIn("tier", nodes[node["id"]])


if __name__ == "__main__":
    unittest.main()
