"""Regression tests for sim/code_health.py.

Written as unittest.TestCase classes, like sim/tests/test_land.py and
sim/tests/test_deposits.py: sim/code_health.py has no dependency on
sim/engine/ or sim/world/, so importing sim/tests/harness.py would pull in
the whole engine for no reason. sim/tests/__main__.py's own _run_topic runs
both styles identically.

THESE TESTS ARE ABOUT THE DETECTORS, NOT ABOUT THE CURRENT STATE OF THIS
CODEBASE. A check asserting "there are 1,337 short-name occurrences today"
would turn every legitimate rename, every new file, and every other agent's
unrelated edit into a test failure - and this repository is worked on by
several agents in the same checkout at once, so a number like that can
change between one run of this file and the next for
reasons that have nothing to do with code_health.py being right or wrong.
Every test below builds a small fixture with a KNOWN answer - a source
string, or a couple of files on disk - and asserts the detector finds
exactly that, on both sides: a positive case AND a negative case, since a
detector that never says "no" is not measuring anything (see this module's
own docstring in code_health.py, "a check that always says clean is noise").

THE HAZARD-WINDOW REGRESSION. The task this file was written for required
proving the duplication detector finds the real, historical case: the
identical hazard-window loop that lived in both sim/engine/fog.py and
sim/engine/society.py before sim/engine/hazard_window.py was extracted (see
`git log --oneline -- sim/engine/hazard_window.py`, and code_health.py's own
module docstring). That proof was done by hand against the pre-extraction
git commit and is not re-run here as an automated test - shelling out to git
history from inside the regression suite would make this topic slow and
would tie it to this repository's specific history rather than to the
detector's general behaviour, and CLAUDE.md section 5 already gives
`prove_rename_safe.py` as the tool for reasoning about specific commits.
Instead, `DuplicationDetectorTests.test_finds_a_near_identical_loop_across_two_files`
below reproduces the SAME SHAPE of bug as a small, self-contained fixture:
two functions in two different files, each opening a for-loop with the same
five-statement window-arithmetic preamble and then doing something different
afterwards - structurally identical to what fog.py and society.py actually
had. Finding it here is the detector proving it would have caught the real
case, without depending on that case continuing to exist in git history.
"""
import os
import shutil
import sys
import tempfile
import textwrap
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from sim import code_health as ch


class _TempRoot(object):
    """A scratch directory standing in for `code_health.ROOT`, so a detector
    can be exercised against known fixture files without ever writing
    anything into the real repository (CLAUDE.md section 6: the tree tools
    have already rewritten a committed file by accident once - this file
    does not repeat that class of mistake, even in its own tests).

    `files` maps a path RELATIVE TO ROOT (e.g. "sim/fixture.py") to its
    source text (auto-dedented, so a fixture can be written indented to
    match the surrounding test code). `ch.ROOT` is restored in `__exit__`
    even if the test body raises, so one failing assertion can never leave
    later tests pointed at a deleted directory.
    """

    def __init__(self, files):
        self.files = files
        self._dir = None
        self._old_root = None

    def __enter__(self):
        self._dir = tempfile.mkdtemp(prefix="code_health_test_")
        for relative_path, content in self.files.items():
            full_path = os.path.join(self._dir, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as handle:
                handle.write(textwrap.dedent(content))
        self._old_root = ch.ROOT
        ch.ROOT = self._dir
        return self._dir

    def __exit__(self, exc_type, exc_value, traceback):
        ch.ROOT = self._old_root
        shutil.rmtree(self._dir, ignore_errors=True)
        return False


# ============================================================================
# NAMES
# ============================================================================

class OccurrenceScanTests(unittest.TestCase):
    """scan_occurrences: method 1, "what a rename tool must touch"."""

    def test_a_rebound_local_counts_once_per_rebinding(self):
        source = """
            def function_under_test():
                k = 1
                k = 2
                k = 3
                return k
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["per_name"]["k"], 3)
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["tier1"], 3, "all three are function-local")

    def test_a_long_name_is_not_counted_at_all(self):
        source = """
            def function_under_test():
                total = 1
                return total
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["total"], 0)
        self.assertEqual(report["per_name"], {})

    def test_underscore_alone_is_never_counted(self):
        source = """
            def function_under_test():
                _ = 1
                for _ in range(3):
                    pass
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["total"], 0)

    def test_files_with_zero_short_names_are_not_counted_as_hits(self):
        source = """
            def function_under_test(argument):
                return argument
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["files_with_hits"], 0)
        self.assertEqual(report["files_scanned"], 1)


class TierClassificationTests(unittest.TestCase):
    """Tier follows docs/architecture/NAMING_PLAN.md A.4: Tier 1 is a
    comprehension target or a function-local assign/for-target/with-as/
    except-as/lambda-param; Tier 2 is a named-function parameter or a
    module-/class-level binding."""

    def test_function_local_assign_is_tier1(self):
        source = """
            def function_under_test():
                k = 1
                return k
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["tier1"], 1)
        self.assertEqual(report["tier2"], 0)

    def test_module_level_assign_is_tier2(self):
        source = """
            k = 1
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["tier2"], 1)
        self.assertEqual(report["tier1"], 0)

    def test_named_function_parameter_is_tier2_even_though_its_body_is_tier1(self):
        source = """
            def function_under_test(k):
                v = k + 1
                return v
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        # k (parameter) -> Tier 2; v (function-local assign) -> Tier 1.
        self.assertEqual(report["tier2"], 1)
        self.assertEqual(report["tier1"], 1)

    def test_lambda_parameter_is_tier1(self):
        source = """
            handler = lambda k: k + 1
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        # "handler" is not short, so the lambda's own parameter "k" is the
        # only short name here - a lambda parameter, so Tier 1.
        self.assertEqual(report["tier1"], 1)
        self.assertEqual(report["tier2"], 0)
        self.assertEqual(report["per_name"], {"k": 1})

    def test_comprehension_target_is_tier1_even_at_module_level(self):
        source = """
            total = [k for k in range(3)]
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        # k is a comprehension target: Tier 1 regardless of the comprehension
        # itself sitting at module scope, because a comprehension is always
        # its own scope.
        self.assertEqual(report["tier1"], 1)
        self.assertEqual(report["per_name"]["k"], 1)

    def test_method_parameter_is_tier2(self):
        source = """
            class Thing(object):
                def method(self, k):
                    return k
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["tier2"], 1)
        self.assertEqual(report["tier1"], 0)


class ExemptionTests(unittest.TestCase):
    """CLAUDE.md section 7's own exemptions: "i" as a loop index, "x"/"y"
    bound together as a coordinate pair. Exempt occurrences still count
    toward `total` (comparable to CLAUDE.md's own 4,972, which also counts
    "i") but not toward `flagged_total`."""

    def test_i_as_a_for_loop_index_is_exempt(self):
        source = """
            def function_under_test():
                for i in range(3):
                    pass
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["total"], 1)
        self.assertEqual(report["exempted"], 1)
        self.assertEqual(report["flagged_total"], 0)

    def test_i_as_a_plain_assignment_is_not_exempt(self):
        source = """
            def function_under_test():
                i = 3
                return i
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        # "i" here is an ordinary assign, not a for-loop index - the
        # exemption is about the ROLE, not the spelling.
        self.assertEqual(report["exempted"], 0)
        self.assertEqual(report["flagged_total"], 1)

    def test_x_and_y_bound_together_are_exempt(self):
        source = """
            def function_under_test():
                x, y = 1, 2
                return x, y
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["exempted"], 2)
        self.assertEqual(report["flagged_total"], 0)

    def test_x_alone_without_y_is_not_exempt(self):
        source = """
            def function_under_test():
                x = 1
                return x
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_occurrences(["sim/fixture.py"])
        self.assertEqual(report["exempted"], 0)
        self.assertEqual(report["flagged_total"], 1)


class NamePerScopeTests(unittest.TestCase):
    """scan_name_per_scope: method 3, one binding per (name, scope), via
    symtable - a name rebound five times in one function counts once."""

    def test_a_rebound_local_counts_once(self):
        source = """
            def function_under_test():
                k = 1
                k = 2
                k = 3
                return k
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_name_per_scope(["sim/fixture.py"])
        self.assertEqual(report["per_name"]["k"], 1)

    def test_the_same_name_in_two_functions_counts_twice(self):
        source = """
            def function_under_test():
                k = 1
                return k

            def second_function():
                k = 2
                return k
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_name_per_scope(["sim/fixture.py"])
        self.assertEqual(report["per_name"]["k"], 2)

    def test_a_parameter_counts_as_a_binding_even_though_it_is_never_assigned(self):
        source = """
            def function_under_test(k):
                return k
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_name_per_scope(["sim/fixture.py"])
        self.assertEqual(report["per_name"]["k"], 1)

    def test_a_comprehensions_implicit_dot_zero_is_an_artifact(self):
        source = """
            total = [k for k in range(3)]
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.scan_name_per_scope(["sim/fixture.py"])
        self.assertGreater(report["total_including_comprehension_artifacts"],
                           report["total_excluding_comprehension_artifacts"])
        self.assertNotIn(".0", report["per_name_excluding_artifacts"])


class ReproductionCheckTests(unittest.TestCase):
    """names_report's own honesty check: does today's number match what
    CLAUDE.md quotes. Exercised against a fixture engineered to match (or
    not match) the reference figures directly, rather than the real
    codebase - which drifts, is the point of this whole file, and is edited
    by other agents concurrently while this suite runs."""

    def test_a_fixture_engineered_to_match_reports_reproduces_true(self):
        # CLAUDE_MD_REFERENCE["k_occurrences"] is 568 across 53 files in the
        # real reference; rather than reproduce that exactly (568 lines of
        # fixture), this pins the MECHANISM: reproduces_claude_md flags a
        # metric true exactly when today's number equals the reference.
        original = dict(ch.CLAUDE_MD_REFERENCE)
        try:
            ch.CLAUDE_MD_REFERENCE["k_occurrences"] = 2
            ch.CLAUDE_MD_REFERENCE["k_files"] = 1
            source = """
                def function_under_test():
                    k = 1
                    k = 2
                    return k
            """
            with _TempRoot({"sim/fixture.py": source}):
                report = ch.names_report(["sim/fixture.py"])
            self.assertTrue(report["reproduces_claude_md"]["k_occurrences"])
            self.assertTrue(report["reproduces_claude_md"]["k_files"])
        finally:
            ch.CLAUDE_MD_REFERENCE.clear()
            ch.CLAUDE_MD_REFERENCE.update(original)

    def test_a_mismatched_fixture_reports_reproduces_false(self):
        original = dict(ch.CLAUDE_MD_REFERENCE)
        try:
            ch.CLAUDE_MD_REFERENCE["k_occurrences"] = 999999
            source = """
                def function_under_test():
                    k = 1
                    return k
            """
            with _TempRoot({"sim/fixture.py": source}):
                report = ch.names_report(["sim/fixture.py"])
            self.assertFalse(report["reproduces_claude_md"]["k_occurrences"])
        finally:
            ch.CLAUDE_MD_REFERENCE.clear()
            ch.CLAUDE_MD_REFERENCE.update(original)

    def test_binding_sites_is_explicitly_unverifiable_not_silently_wrong(self):
        with _TempRoot({"sim/fixture.py": "k = 1\n"}):
            report = ch.names_report(["sim/fixture.py"])
        self.assertIsNone(report["reproduces_claude_md"]["binding_sites_total"])


# ============================================================================
# DUPLICATION
# ============================================================================

# The shared five-statement preamble, reproducing the SHAPE of the real
# pre-extraction hazard-window bug (see this module's own docstring): open a
# collection, bail on an empty marker, compute a start and an end from it,
# bail again once the current position is past the end. Deliberately using
# the same variable names in both fixture files, as the real fog.py and
# society.py both used "yrs"/"year_start"/"year_end" - the normaliser
# discards names anyway, so this is not what makes the match work, but it
# keeps the fixture honest about what the real bug looked like. Held as a
# plain list of UNINDENTED lines and indented programmatically at each call
# site (see _hazard_fixture below) rather than as a pre-indented text block,
# because textwrap.dedent - used throughout this file to let a fixture be
# written indented inside a test method - dedents by the MINIMUM indent
# across an entire string; splicing a separately-indented block in with "%s"
# breaks that measurement and misindents everything around it.
_HAZARD_SHAPED_PREAMBLE_LINES = [
    'window = record.get("years") or []',
    "if not window:",
    "    continue",
    "year_start = window[0]",
    "year_end = window[1] if len(window) > 1 else window[0]",
    "if current_year > year_end:",
    "    continue",
]


def _hazard_fixture(class_name, method_name, setup_line, loop_body_lines, return_line):
    """A complete, correctly-indented Python source file: a class with one
    method that opens a for-loop with `_HAZARD_SHAPED_PREAMBLE_LINES`, then
    `loop_body_lines` (indented to the same depth), then returns."""
    lines = [
        "class %s(object):" % class_name,
        "    def %s(self):" % method_name,
        "        %s" % setup_line,
        '        for record in self.civ.get("hazards") or []:',
    ]
    lines += ["            %s" % line for line in _HAZARD_SHAPED_PREAMBLE_LINES]
    lines += ["            %s" % line for line in loop_body_lines]
    lines.append("        %s" % return_line)
    return "\n".join(lines) + "\n"


class DuplicationDetectorTests(unittest.TestCase):

    def test_finds_a_near_identical_loop_across_two_files(self):
        # Two different files, two functions with different names doing
        # different things with their results, but opening their loop with
        # the exact same five-statement window-arithmetic preamble - the
        # shape of the real, historical fog.py/society.py duplicate.
        file_a = _hazard_fixture(
            "SampleA", "screen_one", "rows = []",
            ["rows.append((year_start, year_end))"], "return rows")
        file_b = _hazard_fixture(
            "SampleB", "screen_two", "urgent = None",
            ['urgent = record.get("name")', "break"], "return urgent")
        with _TempRoot({"sim/a.py": file_a, "sim/b.py": file_b}):
            report = ch.duplication_report(["sim/a.py", "sim/b.py"])
        self.assertGreaterEqual(report["cluster_count"], 1)
        cross_file = [cluster for cluster in report["clusters"]
                     if len({member["path"] for member in cluster["members"]}) >= 2]
        self.assertTrue(cross_file, "expected at least one cross-file cluster; got %r"
                        % report["clusters"])
        # The preamble itself is untouched between the two files (only what
        # comes after it differs), so it must appear as an EXACT clone - not
        # merely a near-duplicate - exactly like the real pre-extraction case.
        self.assertTrue(any(cluster["distinct_versions"] == 1 for cluster in cross_file),
                        "expected an exact (1-version) cross-file cluster")

    def test_unrelated_functions_are_not_clustered(self):
        file_a = """
            def compute_price(base, tax_rate):
                subtotal = base * (1.0 + tax_rate)
                rounded = round(subtotal, 2)
                return rounded

            def compute_price_2(base, tax_rate):
                subtotal2 = base * (1.0 + tax_rate)
                rounded2 = round(subtotal2, 2)
                return rounded2
        """
        file_b = """
            def parse_header(line):
                pieces = line.strip().split(":")
                key = pieces[0].strip()
                value = pieces[1].strip() if len(pieces) > 1 else ""
                return key, value

            def format_duration(seconds):
                minutes = seconds // 60
                remainder = seconds % 60
                return "%dm%ds" % (minutes, remainder)
        """
        with _TempRoot({"sim/a.py": file_a, "sim/b.py": file_b}):
            report = ch.duplication_report(["sim/a.py", "sim/b.py"])
        cross_file = [cluster for cluster in report["clusters"]
                     if len({member["path"] for member in cluster["members"]}) >= 2]
        self.assertEqual(cross_file, [], "unrelated functions should not cluster")

    def test_import_only_preambles_are_not_reported_as_duplicates(self):
        # Every file opens with some mix of docstring + imports; that must
        # not be reported as "duplicated logic" (see _is_boilerplate_window).
        file_a = '''
            """Module A."""
            import os
            import sys
            import json
            import collections
        '''
        file_b = '''
            """Module B."""
            import os
            import sys
            import json
            import collections
        '''
        with _TempRoot({"sim/a.py": file_a, "sim/b.py": file_b}):
            report = ch.duplication_report(["sim/a.py", "sim/b.py"])
        self.assertEqual(report["candidates_scanned"], 0)
        self.assertEqual(report["cluster_count"], 0)

    def test_below_the_size_threshold_is_not_a_candidate_at_all(self):
        file_a = """
            def function_under_test():
                a = 1
                b = 2
                return a + b
        """
        with _TempRoot({"sim/a.py": file_a}):
            candidates = ch._collect_candidates(["sim/a.py"], window=3, min_size=1000)
        self.assertEqual(candidates, [])


# ============================================================================
# COMPLEXITY AND SIZE
# ============================================================================

class ComplexityReportTests(unittest.TestCase):

    def setUp(self):
        if not ch._radon_available():
            self.skipTest("radon is not installed")

    def test_a_deeply_branching_function_is_flagged(self):
        branches = "\n".join(
            "    if n == %d:\n        return %d" % (i, i)
            for i in range(20))
        source = "def function_under_test(n):\n%s\n    return -1\n" % branches
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.complexity_report(["sim/fixture.py"])
        self.assertTrue(report["available"])
        names = [entry["name"] for entry in report["functions_over_threshold"]]
        self.assertIn("function_under_test", names)

    def test_a_trivial_function_is_not_flagged(self):
        source = """
            def function_under_test(n):
                return n + 1
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.complexity_report(["sim/fixture.py"])
        self.assertEqual(report["functions_over_threshold"], [])

    def test_a_long_file_is_flagged_over_the_code_line_threshold(self):
        source = "\n".join("x_%d = %d" % (i, i) for i in range(ch.CODE_LINE_THRESHOLD + 50))
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.complexity_report(["sim/fixture.py"])
        flagged = [entry["path"] for entry in report["files_over_code_lines"]]
        self.assertIn("sim/fixture.py", flagged)

    def test_a_short_file_is_not_flagged(self):
        source = "x = 1\n"
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.complexity_report(["sim/fixture.py"])
        self.assertEqual(report["files_over_code_lines"], [])
        self.assertEqual(report["files_over_total_lines"], [])


class ComplexityDegradesCleanlyTests(unittest.TestCase):
    """When radon is not importable, complexity_report must say so rather
    than crash - the same discipline sim/tests/test_static_checks.py already
    holds ruff to."""

    def test_reports_unavailable_rather_than_raising(self):
        original = ch._radon_available
        ch._radon_available = lambda: False
        try:
            report = ch.complexity_report(["sim/code_health.py"])
        finally:
            ch._radon_available = original
        self.assertEqual(report, {"available": False})
        # Must not raise when handed to the printer either.
        import io
        import contextlib
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            ch.print_complexity_report(report)
        self.assertIn("SKIPPED", buffer.getvalue())


# ============================================================================
# MISCELLANEOUS
# ============================================================================

class LongParameterListTests(unittest.TestCase):

    def test_a_function_with_many_parameters_is_flagged(self):
        params = ", ".join("p%d" % i for i in range(ch.LONG_PARAMETER_THRESHOLD))
        source = "def function_under_test(%s):\n    return 1\n" % params
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.long_parameter_list_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["findings"][0]["name"], "function_under_test")

    def test_self_and_cls_are_not_counted_toward_the_threshold(self):
        params = ", ".join("p%d" % i for i in range(ch.LONG_PARAMETER_THRESHOLD - 1))
        source = """
            class Thing(object):
                def method(self, %s):
                    return 1
        """ % params
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.long_parameter_list_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 0)

    def test_a_short_parameter_list_is_not_flagged(self):
        source = """
            def function_under_test(a, b, c):
                return a + b + c
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.long_parameter_list_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 0)


class LazyGetattrReportTests(unittest.TestCase):

    def test_a_lazy_self_field_read_is_flagged(self):
        source = """
            class Thing(object):
                def has_fog(self):
                    return getattr(self, "fog", False)
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.lazy_getattr_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["findings"][0]["attribute"], "fog")

    def test_a_lazy_read_through_an_attribute_chain_rooted_in_self_is_flagged(self):
        source = """
            class Thing(object):
                def wage(self):
                    return getattr(self.household, "wage_hours", 0)
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.lazy_getattr_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 1)

    def test_getattr_on_an_unrelated_object_is_not_flagged(self):
        source = """
            def describe(other_module):
                return getattr(other_module.thing, "name", "unnamed")
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.lazy_getattr_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 0)

    def test_two_argument_getattr_is_not_flagged(self):
        # No default supplied at all - a different (and unremarkable) idiom,
        # not the "absence is meaningful" pattern this check targets.
        source = """
            class Thing(object):
                def name(self):
                    return getattr(self, "name")
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.lazy_getattr_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 0)


class RuffBackedChecksDegradeCleanlyTests(unittest.TestCase):
    """unused_imports_report / imports_not_at_top_report: must say
    "unavailable" rather than crash when ruff cannot be found - mirrors
    sim/tests/test_static_checks.py's own discipline for the same tool."""

    def test_unused_imports_reports_unavailable_when_ruff_is_missing(self):
        original = ch._ruff_command
        ch._ruff_command = lambda: None
        try:
            report = ch.unused_imports_report(["sim/code_health.py"])
        finally:
            ch._ruff_command = original
        self.assertFalse(report["available"])
        self.assertEqual(report["count"], 0)

    def test_imports_not_at_top_reports_unavailable_when_ruff_is_missing(self):
        original = ch._ruff_command
        ch._ruff_command = lambda: None
        try:
            report = ch.imports_not_at_top_report(["sim/code_health.py"])
        finally:
            ch._ruff_command = original
        self.assertFalse(report["available"])


class RuffBackedChecksFindRealFindingsTests(unittest.TestCase):
    """Live smoke tests against the real ruff binary, skipped (not failed)
    if it is not installed - the same accommodation
    sim/tests/test_static_checks.py makes."""

    def setUp(self):
        if ch._ruff_command() is None:
            self.skipTest("ruff is not installed")

    def test_an_actually_unused_import_is_found(self):
        source = """
            import os
            import sys

            def function_under_test():
                return sys.argv
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.unused_imports_report(["sim/fixture.py"])
        self.assertTrue(report["available"])
        self.assertEqual(report["count"], 1)
        self.assertIn("sim/fixture.py", report["by_file"])

    def test_no_unused_imports_reports_zero(self):
        source = """
            import sys

            def function_under_test():
                return sys.argv
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.unused_imports_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 0)

    def test_a_late_unmarked_import_is_found(self):
        source = """
            x = 1
            import os
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.imports_not_at_top_report(["sim/fixture.py"])
        self.assertTrue(report["available"])
        self.assertEqual(report["count"], 1)

    def test_a_noqa_marked_late_import_is_not_found(self):
        source = """
            x = 1
            import os  # noqa: E402
        """
        with _TempRoot({"sim/fixture.py": source}):
            report = ch.imports_not_at_top_report(["sim/fixture.py"])
        self.assertEqual(report["count"], 0)


# ============================================================================
# DETERMINISM AND READ-ONLY BEHAVIOUR
#
# CLAUDE.md section 6 records a full day lost to id()-reuse nondeterminism,
# and this task's own brief calls out that a burndown tool whose numbers
# move on an unchanged tree is worthless. Both are cheap to pin directly.
# ============================================================================

class DeterminismAndSafetyTests(unittest.TestCase):

    def test_two_runs_against_the_same_fixture_agree_exactly(self):
        source = """
            def function_under_test():
                for i in range(3):
                    k = i
                    for j in range(2):
                        pass
                return k

            class Thing(object):
                def method(self, alpha, beta, gamma, delta, epsilon, zeta, eta):
                    return getattr(self, "cached", None)
        """
        with _TempRoot({"sim/fixture.py": source}):
            first = ch.full_report(["sim/fixture.py"])
            second = ch.full_report(["sim/fixture.py"])
        self.assertEqual(first, second)

    def test_scanning_never_writes_to_the_scanned_tree(self):
        source = "k = 1\n"
        with _TempRoot({"sim/fixture.py": source}) as root:
            before = _snapshot(root)
            ch.full_report(["sim/fixture.py"])
            after = _snapshot(root)
        # ".ruff_cache" is RUFF's own cache directory, created as a side
        # effect of code_health.py shelling out to it (the same thing would
        # happen if a person ran `ruff check` by hand) - not something this
        # file writes itself, and this repository's own .gitignore already
        # excludes it for exactly that reason. Excluded here so this
        # assertion is about code_health.py's own behaviour, not ruff's.
        before = {path: value for path, value in before.items() if ".ruff_cache" not in path}
        after = {path: value for path, value in after.items() if ".ruff_cache" not in path}
        self.assertEqual(before, after)

    def test_record_and_check_agree_on_an_unchanged_fixture(self):
        source = """
            def function_under_test():
                k = 1
                return k
        """
        with _TempRoot({"sim/fixture.py": source}):
            original_python_files = ch.python_files
            ch.python_files = lambda base=None, exclude_dirs=("__pycache__",): ["sim/fixture.py"]
            baseline_path = os.path.join(tempfile.mkdtemp(prefix="code_health_baseline_"),
                                         "baseline.json")
            try:
                self.assertEqual(ch.cmd_record(baseline_path), 0)
                self.assertEqual(ch.cmd_check(baseline_path), 0)
            finally:
                ch.python_files = original_python_files
                shutil.rmtree(os.path.dirname(baseline_path), ignore_errors=True)


def _snapshot(root):
    """path -> mtime/size, for every file under root, used to prove a scan
    touched nothing on disk."""
    out = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            stat = os.stat(full_path)
            out[full_path] = (stat.st_mtime_ns, stat.st_size)
    return out
