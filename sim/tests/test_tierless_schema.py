"""Focused regression tests for the tierless technology schema."""
import copy
import json
import os
import tempfile
import unittest
from unittest import mock

from sim import treetool
from sim import build_index
from sim.engine import data


TIERLESS_BRANCHES = (
    "00_capabilities.json",
    "01_materials.json",
    "10_textiles.json",
    "11_food_agriculture.json",
    "12_household.json",
    "13_media.json",
    "14_land_transport.json",
    "15_ships.json",
    "16_aviation.json",
    "17_energy.json",
    "18_chemicals.json",
    "19_metallurgy_mining.json",
    "20_precision.json",
    "21_medicine.json",
    "22_civil.json",
    "23_optics_instruments.json",
    "24_comms_computing.json",
    "30_expeditions.json",
    "40_finance_institutions.json",
    "41_chemistry_deep.json",
    "42_electrical_deep.json",
    "43_manufacturing_deep.json",
    "44_medicine_deep.json",
    "45a_transport_land_deep.json",
    "45b_transport_rail_marine_deep.json",
    "46_materials_deep.json",
    "47_agri_food_deep.json",
    "48_instruments_deep.json",
    "49_military.json",
    "50_textiles_consumer_deep.json",
    "51_construction_deep.json",
    "52_energy_deep.json",
    "53_information_deep.json",
    "54_science_method_deep.json",
    "60_goalpath_deep.json",
    "62_control_ops_deep.json",
)

TIERLESS_REVIEW_SNAPSHOTS = (
    "AUDIT_SAMPLE.json",
    "caps_batch_0.json",
    "caps_batch_1.json",
    "caps_batch_2.json",
    "caps_batch_3.json",
    "caps_batch_4.json",
)


class TierlessSchemaTests(unittest.TestCase):
    def test_generated_index_does_not_render_tiers(self):
        readme = os.path.join(build_index.KB, "README.md")
        with open(readme) as source:
            text = source.read()
        self.assertNotIn("| Node | Tier |", text)
        self.assertNotIn("| Node | Tier | Your hours | Documented in |", text)

    def test_branch_nodes_are_tierless(self):
        for filename in TIERLESS_BRANCHES:
            with self.subTest(filename=filename):
                path = os.path.join(treetool.BR, filename)
                with open(path) as source:
                    nodes = json.load(source)
                self.assertTrue(nodes)
                self.assertFalse([node["id"] for node in nodes if "tier" in node])

    def test_generated_tree_matches_tierless_sources(self):
        source_ids = set()
        for filename in TIERLESS_BRANCHES:
            with open(os.path.join(treetool.BR, filename)) as source:
                source_ids.update(node["id"] for node in json.load(source))
        with open(data.TREE) as source:
            generated_nodes = json.load(source)["nodes"]
        tiered_ids = {node["id"] for node in generated_nodes if "tier" in node}
        self.assertFalse(source_ids & tiered_ids)

    def test_review_snapshots_are_tierless(self):
        review_dir = os.path.join(data.ROOT, "data", "review")
        for filename in TIERLESS_REVIEW_SNAPSHOTS:
            with self.subTest(filename=filename):
                with open(os.path.join(review_dir, filename)) as source:
                    snapshot = json.load(source)
                self.assertFalse([node.get("id") for node in snapshot
                                  if "tier" in node])

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
        with open(data.TREE) as source:
            tree = json.load(source)
        node = copy.deepcopy(tree["nodes"][0])
        node.pop("tier", None)
        tree["nodes"] = [node]

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as temp_file:
            json.dump(tree, temp_file)
            path = temp_file.name
        try:
            with mock.patch.object(data, "TREE", path):
                _, _, nodes, _, _ = data.load()
            self.assertNotIn("tier", nodes[node["id"]])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
