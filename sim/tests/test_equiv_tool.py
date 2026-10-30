"""The equivalence tool's pure pieces: flatten, relocate, drop ignored, section hashes, leaf diff, first divergence.
Each test calls one function on written-out inputs; no game is built."""
import unittest

from sim.tests import equiv, equiv_core

QUICK_TOPIC = True


class Flatten(unittest.TestCase):
    def test_nested_dicts_and_lists_become_slash_paths_with_float_reprs(self):
        leaves = equiv_core.flatten({"b": [1, {"c": 0.1}], "a": "x", "n": None})
        self.assertEqual(leaves, {"/a": '"x"', "/b/0": "1", "/b/1/c": "0.1", "/n": "null"})

    def test_a_last_bit_change_in_a_float_changes_the_leaf(self):
        self.assertNotEqual(equiv_core.flatten({"v": 0.1}), equiv_core.flatten({"v": 0.1 + 1e-17 * 3}))
        self.assertNotEqual(equiv_core.flatten({"v": 0.1}), equiv_core.flatten({"v": 0.30000000000000004 / 3}))

    def test_empty_containers_are_kept_as_leaves(self):
        self.assertEqual(equiv_core.flatten({"d": {}, "l": []}), {"/d": "{}", "/l": "[]"})

    def test_a_log_record_loses_its_prose_and_keeps_kind_and_facts(self):
        record = {"__log_line__": "wage_cascade", "text": "wages are 2% high", "facts": {"percent": 2}}
        self.assertEqual(equiv_core.flatten({"log": [[100, record]]}),
                         {"/log/0/0": "100", "/log/0/1/__log_line__": '"wage_cascade"', "/log/0/1/facts/percent": "2"})

    def test_key_order_does_not_matter(self):
        self.assertEqual(list(equiv_core.flatten({"b": 1, "a": 2})), ["/a", "/b"])


class Relocate(unittest.TestCase):
    def test_a_moved_prefix_hashes_like_its_old_place(self):
        old = {"/household/capital": "5", "/household/done/0": "1", "/household_other": "9"}
        new = {"/modules/ledger/capital": "5", "/household/done/0": "1", "/household_other": "9"}
        moved = equiv_core.relocate(new, [("/modules/ledger/capital", "/household/capital")])
        self.assertEqual(moved, old)

    def test_rules_apply_in_order_so_a_chain_of_moves_lands_at_the_end(self):
        leaves = {"/a/x": "1"}
        self.assertEqual(equiv_core.relocate(leaves, [("/a", "/b"), ("/b", "/c")]), {"/c/x": "1"})

    def test_no_rules_returns_the_leaves_unchanged(self):
        self.assertEqual(equiv_core.relocate({"/a": "1"}, []), {"/a": "1"})


class DropIgnored(unittest.TestCase):
    def test_a_wildcard_segment_matches_any_seat_and_is_carried_into_the_base_path(self):
        leaves = {"/seats/second/modules/ledger/capital": "5"}
        moved = equiv_core.relocate(leaves, [("/seats/*/modules/ledger/capital", "/seats/*/household/capital")])
        self.assertEqual(moved, {"/seats/second/household/capital": "5"})

    def test_a_wildcard_ignored_prefix_drops_every_seats_slot(self):
        leaves = {"/seats/founder/modules/x": "1", "/seats/second/modules": "{}", "/seats/second/goal": "g"}
        self.assertEqual(equiv_core.drop_ignored(leaves, [("/seats/*/modules", "new")]), {"/seats/second/goal": "g"})

    def test_paths_under_an_ignored_prefix_are_dropped_and_siblings_kept(self):
        leaves = {"/modules/x": "1", "/modules": "{}", "/modules_kept": "2", "/seats/founder/modules/y": "3"}
        kept = equiv_core.drop_ignored(leaves, [("/modules", "new section"), ("/seats/founder/modules", "new")])
        self.assertEqual(kept, {"/modules_kept": "2"})

    def test_a_relocated_field_is_still_compared_when_its_new_home_is_not_ignored(self):
        leaves = {"/modules/ledger/capital": "5", "/modules/assembly": "1"}
        moved = equiv_core.relocate(leaves, [("/modules/ledger/capital", "/household/capital")])
        self.assertEqual(equiv_core.drop_ignored(moved, [("/modules", "bookkeeping")]), {"/household/capital": "5"})


class SectionHashes(unittest.TestCase):
    def test_a_change_in_one_section_changes_only_that_section(self):
        before = equiv_core.section_hashes({"/a/x": "1", "/b/y": "2"})
        after = equiv_core.section_hashes({"/a/x": "1", "/b/y": "3"})
        self.assertEqual(equiv_core.differing_sections(before, after), ["b"])

    def test_the_hash_does_not_depend_on_leaf_insertion_order(self):
        self.assertEqual(equiv_core.section_hashes({"/a/x": "1", "/a/y": "2"}),
                         equiv_core.section_hashes({"/a/y": "2", "/a/x": "1"}))

    def test_a_section_present_on_one_side_only_differs(self):
        self.assertEqual(equiv_core.differing_sections({"a": "1"}, {"a": "1", "b": "2"}), ["b"])


class DiffLeaves(unittest.TestCase):
    def test_differing_missing_and_extra_leaves_are_listed_in_path_order(self):
        base = {"/a": "1", "/b": "2", "/c": "3"}
        current = {"/a": "1", "/b": "9", "/d": "4"}
        shown, total = equiv_core.diff_leaves(base, current)
        self.assertEqual(shown, [("/b", "2", "9"), ("/c", "3", equiv_core.ABSENT), ("/d", equiv_core.ABSENT, "4")])
        self.assertEqual(total, 3)

    def test_the_limit_truncates_the_list_but_not_the_count(self):
        shown, total = equiv_core.diff_leaves({"/a": "1", "/b": "1"}, {"/a": "2", "/b": "2"}, limit=1)
        self.assertEqual((len(shown), total), (1, 2))

    def test_sections_narrow_the_comparison(self):
        shown, total = equiv_core.diff_leaves({"/a/x": "1", "/b/y": "1"}, {"/a/x": "2", "/b/y": "2"}, sections=["b"])
        self.assertEqual(shown, [("/b/y", "1", "2")])


class FirstDivergence(unittest.TestCase):
    def test_equal_runs_have_none(self):
        years = [["r0", {"a": "1"}], ["r1", {"a": "2"}]]
        self.assertIsNone(equiv.first_divergence(years, [list(year) for year in years]))

    def test_a_changed_draw_with_no_changed_section_names_the_generator(self):
        recorded = [["r0", {"a": "1"}], ["r1", {"a": "2"}]]
        got = [["r0", {"a": "1"}], ["rX", {"a": "2"}]]
        self.assertEqual(equiv.first_divergence(recorded, got), (1, [], True, ""))

    def test_a_changed_value_names_year_and_section(self):
        recorded = [["r0", {"a": "1", "b": "1"}], ["r1", {"a": "2", "b": "2"}]]
        got = [["r0", {"a": "1", "b": "1"}], ["r1", {"a": "2", "b": "X"}]]
        self.assertEqual(equiv.first_divergence(recorded, got), (1, ["b"], False, ""))

    def test_a_shorter_run_diverges_where_it_ended(self):
        recorded = [["r0", {}], ["r1", {}]]
        index, _sections, _rng, note = equiv.first_divergence(recorded, recorded[:1])
        self.assertEqual(index, 1)
        self.assertTrue(note)  # presentation: the note is free text, only its presence matters


if __name__ == "__main__":
    unittest.main()
