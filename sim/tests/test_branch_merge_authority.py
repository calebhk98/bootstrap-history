"""The merge of the branch files (`sim/engine/tree_merge.py`).

The branch files are the only source: a merge seeds nothing from an earlier
tree, so editing a branch node always changes the tree, and an id defined by
two different files is an error that names both files and builds nothing
(the same rule `sim/engine/validate_production.py` applies to `data/production/`).
An id listed in `_MERGED_DUPLICATE_IDS.json` stays retired wherever a file
still defines it. Fields no branch schema defaults (`kind`, `_internal`)
are carried through exactly as written.

Every test runs against a temporary branches directory.
"""
import json
import os
import tempfile
import unittest
from unittest import mock

from sim.engine import tree_merge


def _node(node_id, **overrides):
    node = {
        "id": node_id,
        "name": node_id.replace("_", " ").title(),
        "cat": "test",
        "pre": [],
        "note": "A fixture node for the branch-merge-authority regression tests.",
        "ph": 60, "lab": {}, "mat": {}, "cap_hours": 200, "up_hours": 40, "risk": 0.15,
        "rev_hours": 0, "sch": 0, "art": 1, "conf": "C", "kb": "",
    }
    node.update(overrides)
    return node


class BranchMergeAuthorityTests(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.out_path = os.path.join(self.tmpdir, "merged.json")
        self.branches_dir = os.path.join(self.tmpdir, "branches")
        os.makedirs(self.branches_dir)
        patch = mock.patch.object(tree_merge, "BR", self.branches_dir)
        patch.start()
        self.addCleanup(patch.stop)

    def _write_merged_duplicate_ids(self, mapping):
        path = os.path.join(self.branches_dir, tree_merge.MERGED_DUPLICATE_IDS_FILE)
        with open(path, "w") as file:
            json.dump({"_readme": "fixture", "merged_duplicate_ids": mapping}, file)

    def _write_branch(self, filename, nodes):
        with open(os.path.join(self.branches_dir, filename), "w") as file:
            json.dump(nodes, file)

    def _merged(self):
        with open(self.out_path) as file:
            return json.load(file)

    def _merge(self):
        """(1, the problems) when `merge_problems` refuses the merge; otherwise (0, the ordinary
        errors) with the merged tree written to `out_path`."""
        self.built = tree_merge.build_tree()
        problems = tree_merge.merge_problems(self.built)
        if problems:
            return 1, "\n".join(problems)
        with open(self.out_path, "w") as file:
            json.dump(self.built.tree, file, indent=2)
        return 0, "\n".join(self.built.errs)

    def test_merge_is_a_fixed_point_with_no_branch_edits(self):
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", cap_hours=150, ph=50),
            _node("fx_beta", pre=["fx_alpha"], cap_hours=300),
        ])
        self.assertEqual(self._merge()[0], 0)
        with open(self.out_path, "rb") as file:
            first = file.read()
        self.assertEqual(self._merge()[0], 0)
        with open(self.out_path, "rb") as file:
            self.assertEqual(first, file.read())

    def test_merge_applies_one_edited_field_and_nothing_else(self):
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", cap_hours=150, ph=50),
            _node("fx_beta", pre=["fx_alpha"], cap_hours=300),
        ])
        self.assertEqual(self._merge()[0], 0)
        before = {node["id"]: node for node in self._merged()["nodes"]}

        self._write_branch("10_fixture.json", [
            _node("fx_alpha", cap_hours=424242.0, ph=50),
            _node("fx_beta", pre=["fx_alpha"], cap_hours=300),
        ])
        self.assertEqual(self._merge()[0], 0)
        after = {node["id"]: node for node in self._merged()["nodes"]}

        changed_fields = {field for field in set(before["fx_alpha"]) | set(after["fx_alpha"])
                          if before["fx_alpha"].get(field) != after["fx_alpha"].get(field)}
        self.assertEqual(changed_fields, {"cap_hours"})
        self.assertEqual(after["fx_alpha"]["cap_hours"], 424242.0)
        self.assertEqual(before["fx_beta"], after["fx_beta"])

    def test_fields_without_a_schema_default_pass_through_as_written(self):
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", kind="INSTITUTION", _internal="audit marker")])
        self.assertEqual(self._merge()[0], 0)
        merged = {node["id"]: node for node in self._merged()["nodes"]}["fx_alpha"]
        self.assertEqual(merged["kind"], "INSTITUTION")
        self.assertEqual(merged["_internal"], "audit marker")

    def test_nodes_come_only_from_branch_files(self):
        self._write_branch("10_fixture.json", [_node("fx_alpha")])
        self.assertEqual(self._merge()[0], 0)
        self.assertEqual([node["id"] for node in self._merged()["nodes"]], ["fx_alpha"])

    def test_meta_comes_from_the_branch_metadata_file(self):
        self._write_branch("10_fixture.json", [_node("fx_alpha")])
        with open(os.path.join(self.branches_dir, tree_merge.META_FILE), "w") as file:
            json.dump({"goal_node": "fx_alpha", "goals": [{"node": "fx_alpha"}]}, file)
        self.assertEqual(self._merge()[0], 0)
        self.assertEqual(self._merged()["meta"]["goal_node"], "fx_alpha")
        self.assertEqual([node["id"] for node in self._merged()["nodes"]], ["fx_alpha"])

    def test_id_defined_in_two_branch_files_is_a_refused_collision(self):
        self._write_branch("10_first.json", [_node("fx_shared", cap_hours=150)])
        self._write_branch("20_second.json", [_node("fx_shared", cap_hours=999)])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1, "a cross-file collision must refuse, "
                                "not silently pick a winner")
        self.assertIn("fx_shared", out)
        self.assertIn("10_first.json", out)
        self.assertIn("20_second.json", out)
        self.assertFalse(os.path.exists(self.out_path))

    def test_id_defined_twice_in_the_same_branch_file_is_also_a_collision(self):
        self._write_branch("10_fixture.json", [
            _node("fx_dup", cap_hours=150), _node("fx_dup", cap_hours=999),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("fx_dup", out)
        self.assertIn("twice in 10_fixture.json", out)

    def test_retired_id_is_not_a_collision_even_when_two_files_still_define_it(self):
        """An id already retired project-wide is not a collision to referee: neither
        definition is applied and the id stays out of the tree."""
        self._write_branch("00_survivor.json", [_node("tl_survivor", cap_hours=300)])
        self._write_merged_duplicate_ids({"fx_retired": "tl_survivor"})
        self._write_branch("10_first.json", [_node("fx_retired", cap_hours=222)])
        self._write_branch("20_second.json", [_node("fx_retired", cap_hours=333)])

        return_code, out = self._merge()

        self.assertEqual(return_code, 0)
        self.assertEqual({node["id"] for node in self._merged()["nodes"]}, {"tl_survivor"})

    def test_missing_required_field_is_still_an_ordinary_error_not_a_collision(self):
        self._write_branch("10_fixture.json", [
            {"id": "fx_broken", "name": "Broken", "cat": "test"},  # no pre/note
        ])
        return_code, out = self._merge()
        self.assertEqual(return_code, 0)
        self.assertIn("missing fields", out)

    def test_missing_merged_duplicate_ids_file_is_treated_as_empty(self):
        self._write_branch("10_fixture.json", [_node("fx_alpha")])
        return_code, out = self._merge()
        self.assertEqual(return_code, 0, out)
        self.assertEqual(tree_merge.load_merged_duplicate_ids(), {})

    def test_merge_writes_dedup_mapping_from_source_into_tree_meta(self):
        self._write_branch("00_survivor.json", [_node("tl_survivor", cap_hours=300)])
        self._write_merged_duplicate_ids({"fx_retired": "tl_survivor"})
        self._write_branch("10_fixture.json", [_node("fx_new")])
        return_code, out = self._merge()
        self.assertEqual(return_code, 0, out)
        self.assertEqual(self._merged()["meta"]["merged_duplicate_ids"],
                         {"fx_retired": "tl_survivor"})

    def test_undeclared_material_refuses_without_the_override(self):
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", mat={"unobtainium_kg": 3}),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("undeclared_material", out)
        self.assertIn("UNDECLARED material 'unobtainium_kg'", out)
        self.assertFalse(os.path.exists(self.out_path))

    def test_a_refused_merge_still_reports_every_event_and_drops_what_it_names(self):
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", mat={"unobtainium_kg": 3}, lab={"nonexistent_trade": 5}),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("UNDECLARED material 'unobtainium_kg'", out)
        self.assertIn("unknown trade 'nonexistent_trade'", out)
        nodes = {node["id"]: node for node in self.built.tree["nodes"]}
        self.assertEqual(nodes["fx_alpha"]["mat"], {})
        self.assertEqual(nodes["fx_alpha"]["lab"], {})

    def test_unresolvable_prerequisite_is_a_refused_data_loss_event(self):
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", pre=["nonexistent_prereq"]),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("unresolvable_prerequisite", out)
        self.assertIn("dropped unresolvable prereq 'nonexistent_prereq'", out)

    def test_dependency_cycle_is_a_refused_data_loss_event(self):
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", pre=["fx_beta"]),
            _node("fx_beta", pre=["fx_alpha"]),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("dependency_cycle", out)
        self.assertIn("CYCLE broken", out)


class RealBranchCorpusMergesCleanly(unittest.TestCase):
    """The real branch files merge with no collision and no data-loss event."""

    def test_real_merge_reports_nothing_lost(self):
        self.assertEqual(tree_merge.merge_problems(tree_merge.build_tree()), [])


if __name__ == "__main__":
    unittest.main()
