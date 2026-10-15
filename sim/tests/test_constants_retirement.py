"""A new temporary heuristic must name what retires it (Complaints/closed/509).

Declarations are collected the way `sim/constants.py --burndown` collects them, so a heuristic declared
in any listed module is seen. Names in data/review/heuristic_baseline.txt predate the rule.
"""
import sys
import unittest

from sim import constants
from sim import constants_retirement as retirement

QUICK_TOPIC = True


def _filled_registry():
    constants._import_declaring_modules()
    constants._adopt_the_canonical_registry()
    return constants.REGISTRY


class RetirementRuleTests(unittest.TestCase):

    def test_a_promise_outside_the_baseline_names_its_retirement(self):
        missing = retirement.missing_retirement(_filled_registry(), retirement.read_baseline())
        self.assertEqual(missing, [], (
            "declare(..., retire='<complaint number or the mechanism that replaces it>') on: %s"
            % ", ".join(missing)))

    def test_baseline_names_no_longer_declared_are_reported(self):
        stale = retirement.stale_baseline(_filled_registry(), retirement.read_baseline())
        if stale:
            print("heuristic baseline lists %d retired names; run "
                  "`python3 sim/constants.py --prune-baseline`: %s" % (len(stale), ", ".join(stale)),
                  file=sys.stderr)

    def test_baseline_is_sorted_and_unique_so_merges_conflict_rarely(self):
        names = retirement.read_baseline()
        self.assertEqual(names, sorted(set(names)))

    def test_placeholders_do_not_count_as_a_retirement(self):
        for placeholder in (None, "", "  ", "TODO", "tbd"):
            self.assertFalse(retirement.has_retirement({"retire": placeholder}), placeholder)
        self.assertTrue(retirement.has_retirement({"retire": "Complaints/507"}))

    def test_a_new_unlabelled_heuristic_is_caught(self):
        registry = {"OLD": {"kind": "temporary_heuristic", "retire": None},
                    "NEW": {"kind": "temporary_heuristic", "retire": None},
                    "FACT": {"kind": "physical_constant", "retire": None},
                    "GOOD": {"kind": "temporary_heuristic", "retire": "mechanism x"}}
        self.assertEqual(retirement.missing_retirement(registry, ["OLD"]), ["NEW"])

    def test_declare_records_retire(self):
        constants.declare("RETIREMENT_TEST_ONLY_NUMBER", 1.0, kind="temporary_heuristic",
                          unit="1", why="test", retire="Complaints/509")
        try:
            self.assertEqual(constants.REGISTRY["RETIREMENT_TEST_ONLY_NUMBER"]["retire"],
                             "Complaints/509")
        finally:
            constants.REGISTRY.pop("RETIREMENT_TEST_ONLY_NUMBER", None)


if __name__ == "__main__":
    unittest.main()
