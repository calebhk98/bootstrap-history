"""A capability name is a prerequisite (`pre`), never the capital field."""

QUICK_TOPIC = True

import glob
import json
import os
import unittest

BRANCH_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "data", "branches")


class CapitalFieldIsANumber(unittest.TestCase):

    def test_no_branch_node_carries_text_under_cap(self):
        offenders = []
        for path in glob.glob(os.path.join(BRANCH_DIRECTORY, "[0-9]*.json")):
            with open(path) as handle:
                for node in json.load(handle):
                    if isinstance(node, dict) and "cap" in node:
                        offenders.append(node.get("id"))
        self.assertEqual(offenders, [])

    def test_capability_prerequisites_are_named_in_pre(self):
        path = os.path.join(BRANCH_DIRECTORY, "50_textiles_consumer_deep.json")
        with open(path) as handle:
            nodes = {node["id"]: node for node in json.load(handle)}
        self.assertIn("cap_tol_1mm", nodes["tx2_flyer"]["pre"])


if __name__ == "__main__":
    unittest.main()
