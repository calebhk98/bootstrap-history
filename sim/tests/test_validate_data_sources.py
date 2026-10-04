"""`simulator.py validate` reports bad production data and branch merges, and neither check reads
the deleted price book."""
import builtins
import json
import os
import tempfile
import unittest
from unittest import mock

from sim.engine import tree_merge, validate_production
from sim.engine.tree_source import load_base_tree
from sim.ui import cli


def _node(node_id):
    return {"id": node_id, "name": node_id, "cat": "test", "pre": [],
            "note": "A fixture node for the validate data-source tests."}


class ValidateReportsMergeProblemsTests(unittest.TestCase):

    def test_a_collision_in_the_branch_files_is_a_validate_error(self):
        branches = tempfile.mkdtemp()
        for filename in ("10_first.json", "20_second.json"):
            with open(os.path.join(branches, filename), "w") as handle:
                json.dump([_node("fx_shared")], handle)
        nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        with mock.patch.object(tree_merge, "BR", branches):
            errors = cli._data_source_errors(nodes)
        self.assertTrue([error for error in errors
                         if error.startswith("data/branches: collision") and "fx_shared" in error],
                        errors)

    def test_the_real_data_has_no_data_source_errors(self):
        nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        self.assertEqual(cli._data_source_errors(nodes), [])


class NoPriceBookTests(unittest.TestCase):

    def test_both_checks_run_with_the_price_book_unreadable(self):
        nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        real_open = builtins.open

        def guarded_open(path, *args, **kwargs):
            if str(path).endswith("prices.json"):
                raise FileNotFoundError(path)
            return real_open(path, *args, **kwargs)

        with mock.patch.object(builtins, "open", guarded_open):
            self.assertEqual(validate_production.production_problems(nodes), [])
            self.assertEqual(tree_merge.merge_problems(tree_merge.build_tree()), [])


if __name__ == "__main__":
    unittest.main()
