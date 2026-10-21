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

    def test_retirement_names_the_complaints_it_cites(self):
        self.assertEqual(retirement.cited_complaints("Complaints/486: a ruler's valuation"), {486})
        self.assertEqual(retirement.cited_complaints("Complaint 620 follow-up, then Complaints/closed/509"), {620, 509})
        self.assertEqual(retirement.cited_complaints("a soil water and nitrate balance"), set())

    def test_a_retirement_citing_only_closed_complaints_is_caught(self):
        registry = {"DANGLING": {"kind": "temporary_heuristic", "retire": "Complaints/544"},
                    "LIVE": {"kind": "temporary_heuristic", "retire": "Complaints/543"},
                    "ONE_LIVE": {"kind": "temporary_heuristic", "retire": "Complaints/544 then Complaints/543"},
                    "MECHANISM": {"kind": "temporary_heuristic", "retire": "a crop growth model"},
                    "FACT": {"kind": "physical_constant", "retire": "Complaints/544"}}
        self.assertEqual(retirement.closed_retirements(registry, open_numbers={543}), ["DANGLING"])

    def test_no_declared_retirement_cites_only_closed_complaints(self):
        dangling = retirement.closed_retirements(_filled_registry(), retirement.open_complaint_numbers())
        self.assertEqual(dangling, [], "retire names only closed complaints; point it at the open complaint that "
                                       "now owns the mechanism: %s" % ", ".join(dangling))

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
