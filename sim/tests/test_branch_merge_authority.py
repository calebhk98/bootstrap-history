"""Pins the fix for Complaints/30: `treetool.py merge` used to seed every node
from the CURRENT `data/tech_tree.json` and then only ADD branch ids it had
never seen before, so editing a branch file's copy of an EXISTING node and
re-merging changed nothing. Demonstrated there: a branch said cap = 424242.0
and the merged tree kept cap = 1500.0, silently.

The fix has two parts and this file pins both:

1. A branch node whose id the tree already carries now OVERWRITES that node,
   field by field, instead of being skipped. It is a field-level overlay, not
   a wipe-and-replace, because the tree carries keys no branch schema has ever
   had a slot for - `kind`, `kb_level`, `_total_cost`, `_internal` - written
   directly onto `data/tech_tree.json` by `judge`/`repair`/`apply-caps` and
   never meant to round-trip through branches (see `cmd_repair`'s docstring
   and `sim/treetool.py`'s own REPAIR PASS comment). Replacing the whole node
   would silently erase every one of those on every edited id; measured
   against the real tree with this fix's field-level overlay, none of them
   move, only genuinely branch-authored fields do.

2. An id defined by TWO DIFFERENT branch files in the same merge run is an
   ERROR that names both files and refuses to write, rather than the old
   "duplicate id, keeping the first" warning buried among ~3,200 others. This
   is the identical rule `sim/validate_production.py`'s `load_production`
   already enforces for `data/production/` (a key defined twice is an error,
   not a silent pick), applied to `data/branches/` for the first time.

An id `meta.merged_duplicate_ids` has already retired stays a `retired`
warning either way, in one file or two: it is not this file's job to decide
which of two definitions of an ALREADY-DEAD id should win, only to keep
resurrecting neither of them, exactly as the unfixed merge already did.

The acceptance test the complaint's "CRITICAL SAFETY" section asks for -
merge with no branch edits reproduces the tree byte for byte, and merge with
one deliberate edit changes exactly that field - is proven here against a
small, fully isolated fixture (a temp tree plus a temp `data/branches/`
directory), not against the real 2,864-node tree: the real tree and the real
branches have been known to disagree on ~1,970 fields since this complaint's
own drift count (see its "The drift, counted" section), almost entirely
because `judge`/`repair`/`apply-caps` write fields no branch has ever carried
and because branch authors have been silently ignored for years. A fixture
proves the MECHANISM is exact; it does not launder that backlog into a
by-the-way side effect of a test run.
"""
import contextlib
import io
import json
import os
import tempfile
import types
import unittest
from unittest import mock

from sim import treetool


def _tree(nodes):
    # merged_duplicate_ids is read from
    # data/branches/_MERGED_DUPLICATE_IDS.json (see
    # treetool.load_merged_duplicate_ids), not from tree meta. The fixture
    # tree still carries the key in meta because cmd_merge writes it back
    # there every run; a test that cares about the retired-id mapping
    # sets it up via
    # BranchMergeAuthorityTests._write_merged_duplicate_ids instead of here.
    return {
        "meta": {"merged_duplicate_ids": {}},
        "nodes": nodes,
    }


def _node(node_id, **overrides):
    node = {
        "id": node_id,
        "name": node_id.replace("_", " ").title(),
        "cat": "test",
        "pre": [],
        "note": "A fixture node for the branch-merge-authority regression tests.",
        "ph": 60, "lab": {}, "mat": {}, "cap": 200, "up": 40, "risk": 0.15,
        "rev": 0, "sch": 0, "art": 1, "conf": "C", "kb": "",
    }
    node.update(overrides)
    return node


class BranchMergeAuthorityTests(unittest.TestCase):
    """Every test runs merge against a temp tree and a temp branches/ dir, via
    mock.patch.object exactly like test_tierless_schema.py does for data.TREE,
    so nothing here ever touches the real data/tech_tree.json or
    data/branches/*.json."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tree_path = os.path.join(self.tmpdir, "tech_tree.json")
        self.branches_dir = os.path.join(self.tmpdir, "branches")
        os.makedirs(self.branches_dir)
        self.patches = [
            mock.patch.object(treetool, "TREE", self.tree_path),
            mock.patch.object(treetool, "BR", self.branches_dir),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)
        # No _MERGED_DUPLICATE_IDS.json is written here on purpose: a
        # fixture branches dir with no such file is exactly the "nobody has
        # deduped anything yet" case, and treetool.load_merged_duplicate_ids
        # must treat that as an empty mapping, not an error (see
        # test_missing_merged_duplicate_ids_file_is_treated_as_empty below).
        # Only a test that cares about a retired id calls
        # _write_merged_duplicate_ids to give it one.

    def _write_merged_duplicate_ids(self, mapping):
        path = os.path.join(self.branches_dir, treetool.MERGED_DUPLICATE_IDS_FILE)
        with open(path, "w") as file:
            json.dump({"_readme": "fixture", "merged_duplicate_ids": mapping}, file)

    def _write_tree(self, tree):
        with open(self.tree_path, "w") as file:
            json.dump(tree, file)

    def _write_branch(self, filename, nodes):
        with open(os.path.join(self.branches_dir, filename), "w") as file:
            json.dump(nodes, file)

    def _read_tree(self):
        with open(self.tree_path) as file:
            return json.load(file)

    def _merge(self, write=True, accept_data_loss=False):
        """Run a merge against this test's own fixture tree.

        `write=True` by default, which is the opposite of treetool's own CLI
        default and is deliberate: every test below is about what the merge
        WRITES, so each one has to ask for the write explicitly now that
        reporting is the default. The one check that is genuinely about the
        report rather than the result passes `write=False` and says so.

        The fixture tree is a temporary file (see setUp's mock.patch of
        treetool.TREE), so a write here cannot reach the repository's own
        data/tech_tree.json.
        """
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            return_code = treetool.cmd_merge(types.SimpleNamespace(
                write=write, accept_data_loss=accept_data_loss))
        return return_code, buf.getvalue()

    # ---- acceptance test 1: no branch edits -> byte-identical tree --------
    def test_merge_is_a_fixed_point_with_no_branch_edits(self):
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", cap=150, ph=50),
            _node("fx_beta", pre=["fx_alpha"], cap=300),
        ])

        rc1, _ = self._merge()
        self.assertEqual(rc1, 0)
        tree_v1 = self._read_tree()

        # Re-run with the SAME, unedited branch file. If a branch edit to an
        # already-known id were still being discarded, this would already be
        # true trivially; the point is that it is ALSO true now that an edit
        # takes effect - re-merging unedited input must be a no-op.
        rc2, _ = self._merge()
        self.assertEqual(rc2, 0)
        tree_v2 = self._read_tree()

        self.assertEqual(tree_v1, tree_v2)
        # Byte-identical, not just structurally equal: re-serialise and
        # compare the actual bytes `_write_json` produced.
        with open(self.tree_path, "rb") as file:
            bytes_v2 = file.read()
        json.dump(tree_v1, open(self.tree_path + ".v1", "w"), indent=1)
        with open(self.tree_path + ".v1", "rb") as file:
            bytes_v1_reserialised = file.read()
        self.assertEqual(bytes_v1_reserialised, bytes_v2)

    # ---- acceptance test 2: one deliberate edit changes exactly that field
    def test_merge_applies_one_edited_field_and_nothing_else(self):
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", cap=150, ph=50),
            _node("fx_beta", pre=["fx_alpha"], cap=300),
        ])
        rc1, _ = self._merge()
        self.assertEqual(rc1, 0)
        before = {node["id"]: node for node in self._read_tree()["nodes"]}

        # This is the complaint's own demonstration, reproduced: edit ONE
        # field of an id the tree already has, on the branch file, and
        # nothing else.
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", cap=424242.0, ph=50),
            _node("fx_beta", pre=["fx_alpha"], cap=300),
        ])
        rc2, out2 = self._merge()
        self.assertEqual(rc2, 0)
        # Both fx_alpha and fx_beta already existed from the first merge, so
        # both are counted as updated even though only fx_alpha's content
        # actually changed - "updated" means "a branch definition of an
        # already-known id was applied", same as "added" already counts every
        # brand-new id regardless of whether anyone will call it interesting.
        self.assertIn("2 updated from branches", out2)
        after = {node["id"]: node for node in self._read_tree()["nodes"]}

        # The edited node: only `cap` differs.
        changed_fields = {field for field in set(before["fx_alpha"]) | set(after["fx_alpha"])
                          if before["fx_alpha"].get(field) != after["fx_alpha"].get(field)}
        self.assertEqual(changed_fields, {"cap"})
        self.assertEqual(after["fx_alpha"]["cap"], 424242.0)

        # Every other node: byte-for-byte unchanged.
        self.assertEqual(before["fx_beta"], after["fx_beta"])

    def test_merge_reports_added_versus_updated_separately(self):
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [_node("fx_alpha")])
        _, out1 = self._merge()
        self.assertIn("1 added from branches", out1)
        self.assertIn("0 updated from branches", out1)

        self._write_branch("10_fixture.json", [_node("fx_alpha", cap=999),
                                                 _node("fx_new")])
        _, out2 = self._merge()
        self.assertIn("1 added from branches", out2)
        self.assertIn("1 updated from branches", out2)

    # ---- repair/judge-only fields must survive a branch overwrite ---------
    def test_branch_overwrite_preserves_fields_no_branch_schema_sets(self):
        """`kind`, `kb_level`, `_total_cost` and `_internal` are written
        straight onto tech_tree.json by judge/repair/apply-caps and never
        appear in `treetool.DEFAULTS` or `treetool.REQUIRED` - a branch file
        has no slot for them. A field-level overwrite must leave them alone
        for every id whose branch definition doesn't mention them; a
        wholesale node replacement (the first, wrong, design tried while
        building this fix) erases them on every edited id instead."""
        tree_node = _node("fx_alpha", cap=150)
        tree_node.update({"kind": "INSTITUTION", "kb_level": "module",
                          "_total_cost": 1234.5, "_internal": "repair-only marker"})
        self._write_tree(_tree([tree_node]))
        self._write_branch("10_fixture.json", [_node("fx_alpha", cap=999)])

        return_code, _ = self._merge()
        self.assertEqual(return_code, 0)
        merged = {node["id"]: node for node in self._read_tree()["nodes"]}["fx_alpha"]

        self.assertEqual(merged["cap"], 999)                    # the edit took effect
        self.assertEqual(merged["kind"], "INSTITUTION")         # repair-only field kept
        self.assertEqual(merged["kb_level"], "module")
        self.assertEqual(merged["_total_cost"], 1234.5)
        self.assertEqual(merged["_internal"], "repair-only marker")

    # ---- the collision rule -------------------------------------------
    def test_id_defined_in_two_branch_files_is_a_refused_collision(self):
        self._write_tree(_tree([]))
        with open(self.tree_path, "rb") as file:
            tree_before = file.read()
        self._write_branch("10_first.json", [_node("fx_shared", cap=150)])
        self._write_branch("20_second.json", [_node("fx_shared", cap=999)])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1, "a cross-file collision must refuse to write, "
                                "not silently pick a winner")
        self.assertIn("MERGE REFUSED", out)
        self.assertIn("fx_shared", out)
        self.assertIn("10_first.json", out)
        self.assertIn("20_second.json", out)
        with open(self.tree_path, "rb") as file:
            tree_after = file.read()
        self.assertEqual(tree_before, tree_after,
                         "a refused merge must not write the tree at all")

    def test_id_defined_twice_in_the_same_branch_file_is_also_a_collision(self):
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [
            _node("fx_dup", cap=150), _node("fx_dup", cap=999),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("fx_dup", out)
        self.assertIn("twice in 10_fixture.json", out)

    def test_retired_id_is_not_a_collision_even_when_two_files_still_define_it(self):
        """Pins the real case this complaint names: lnd_whippletree is
        defined in both data/branches/14_land_transport.json and
        data/branches/55_realism_part02.json, but it is ALSO a key in
        meta.merged_duplicate_ids (retired into tl_whippletree) - discovered,
        not assumed, while doing this work; see Complaints/30's update. An
        id that is already dead project-wide is not a collision to referee,
        it is the SAME "was merged into X, skipping" warning either file gets
        on its own, and it must not block the merge or overwrite anything."""
        surviving = _node("tl_survivor", cap=300)
        retired_zombie = _node("fx_retired", cap=111)
        self._write_tree(_tree([surviving, retired_zombie]))
        self._write_merged_duplicate_ids({"fx_retired": "tl_survivor"})
        self._write_branch("10_first.json", [_node("fx_retired", cap=222)])
        self._write_branch("20_second.json", [_node("fx_retired", cap=333)])

        return_code, out = self._merge()

        self.assertEqual(return_code, 0)
        self.assertNotIn("MERGE REFUSED", out)
        nodes = {node["id"]: node for node in self._read_tree()["nodes"]}
        # Neither branch definition of a retired id is applied - the zombie
        # node, if the tree still carries one, is left exactly as it was.
        self.assertEqual(nodes["fx_retired"]["cap"], 111)

    def test_missing_required_field_is_still_an_ordinary_error_not_a_collision(self):
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [
            {"id": "fx_broken", "name": "Broken", "cat": "test"},  # no pre/note
        ])
        return_code, out = self._merge()
        self.assertEqual(return_code, 0)  # unrelated to the collision rule; unchanged behaviour
        self.assertIn("missing fields", out)

    # ---- the dedup source file (Task 2) --------------------------------
    def test_missing_merged_duplicate_ids_file_is_treated_as_empty(self):
        """No data/branches/_MERGED_DUPLICATE_IDS.json at all - setUp never
        writes one - must mean "nothing has been deduped", not a crash. A
        from-scratch branches/ directory with no dedup history yet is a
        legitimate state, not a malformed one."""
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [_node("fx_alpha")])
        return_code, out = self._merge()
        self.assertEqual(return_code, 0, out)
        self.assertEqual(treetool.load_merged_duplicate_ids(), {})

    def test_merge_writes_dedup_mapping_from_source_into_tree_meta(self):
        """Task 2: the merge reads merged_duplicate_ids from
        data/branches/_MERGED_DUPLICATE_IDS.json and writes it into
        tech_tree.json's meta, same as before - only the SOURCE of that
        mapping moved, not where it ends up."""
        surviving = _node("tl_survivor", cap=300)
        self._write_tree(_tree([surviving]))
        self._write_merged_duplicate_ids({"fx_retired": "tl_survivor"})
        self._write_branch("10_fixture.json", [_node("fx_new")])
        return_code, out = self._merge()
        self.assertEqual(return_code, 0, out)
        meta = self._read_tree()["meta"]
        self.assertEqual(meta["merged_duplicate_ids"], {"fx_retired": "tl_survivor"})

    # ---- the data-loss refusal (Task 1) --------------------------------
    def test_unpriced_material_refuses_to_write_without_the_override(self):
        self._write_tree(_tree([]))
        with open(self.tree_path, "rb") as file:
            tree_before = file.read()
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", mat={"unobtainium_kg": 3}),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("MERGE REFUSED", out)
        self.assertIn("unpriced_material", out)
        self.assertIn("UNPRICED material 'unobtainium_kg'", out)
        self.assertIn("--accept-data-loss", out)
        with open(self.tree_path, "rb") as file:
            tree_after = file.read()
        self.assertEqual(tree_before, tree_after,
                         "a refused merge must not write the tree at all")

    def test_accept_data_loss_writes_anyway_and_still_reports_every_event(self):
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", mat={"unobtainium_kg": 3}, lab={"nonexistent_trade": 5}),
        ])

        return_code, out = self._merge(accept_data_loss=True)

        self.assertEqual(return_code, 0)
        self.assertNotIn("MERGE REFUSED", out)
        self.assertIn("UNPRICED material 'unobtainium_kg'", out)
        self.assertIn("unknown trade 'nonexistent_trade'", out)
        nodes = {node["id"]: node for node in self._read_tree()["nodes"]}
        self.assertIn("fx_alpha", nodes)
        # the dropped material and trade are genuinely gone from the node,
        # not merely warned about - --accept-data-loss accepts the loss, it
        # does not make the unpriced material or unknown trade usable
        self.assertEqual(nodes["fx_alpha"]["mat"], {})
        self.assertEqual(nodes["fx_alpha"]["lab"], {})

    def test_unresolvable_prerequisite_is_a_refused_data_loss_event(self):
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", pre=["nonexistent_prereq"]),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("MERGE REFUSED", out)
        self.assertIn("unresolvable_prerequisite", out)
        self.assertIn("dropped unresolvable prereq 'nonexistent_prereq'", out)

    def test_dependency_cycle_is_a_refused_data_loss_event(self):
        self._write_tree(_tree([]))
        self._write_branch("10_fixture.json", [
            _node("fx_alpha", pre=["fx_beta"]),
            _node("fx_beta", pre=["fx_alpha"]),
        ])

        return_code, out = self._merge()

        self.assertEqual(return_code, 1)
        self.assertIn("MERGE REFUSED", out)
        self.assertIn("dependency_cycle", out)
        self.assertIn("CYCLE broken", out)


class RealBranchCorpusHasNoUnresolvedCollisions(unittest.TestCase):
    """An integration-level smoke test against the REAL data/branches/*.json
    and data/tech_tree.json, run with --dry-run so nothing is written. It
    exists so that a future branch file which reintroduces a same-id
    collision - the mistake this whole complaint is about, just from the
    other direction - fails the suite instead of being merged silently."""

    def test_real_merge_dry_run_finds_no_collisions(self):
        # --accept-data-loss because the real branch corpus DOES currently
        # trigger data-loss events (unpriced materials, unknown trades,
        # unresolvable prerequisites - see Task 1 of the pass that added
        # this flag) and refusing to write for THOSE is correct, working
        # behaviour, not a collision. This test is only about collisions:
        # an id claimed by two different branch files in the same run.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            # write=False: this check reads the REAL data/branches/ corpus
            # rather than a fixture, so it must not write, and it only cares
            # about what the merge REPORTS. That is treetool's own default
            # now, stated here anyway because a reader of this line should
            # not have to know the default to see that it is safe.
            return_code = treetool.cmd_merge(types.SimpleNamespace(
                write=False, accept_data_loss=True))
        self.assertEqual(return_code, 0, "the real branch corpus has an id defined in "
                                "more than one file:\n" + buf.getvalue())
        self.assertNotIn("COLLISION", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
