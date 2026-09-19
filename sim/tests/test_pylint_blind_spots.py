"""Regression tests for sim/pylint_blind_spots.py.

Written as unittest.TestCase classes for the same reason
sim/tests/test_code_health.py is: the scanner has no dependency on
sim/engine/ or sim/world/, so importing sim/tests/harness.py would pull in
the whole engine for no reason. sim/tests/__main__.py's _run_topic runs both
styles identically.

THESE TESTS ARE ABOUT THE DETECTORS, NOT ABOUT TODAY'S COUNT. "476 sites
under sim/" is a fact about the codebase this afternoon, and several agents
edit this checkout at once, so asserting it here would fail for reasons that
have nothing to do with the scanner being right. Every fixture below has a
known answer.

THE CROSS-CHECK IS THE POINT. This scanner's whole reason to exist is the
claim that pylint reports nothing for three kinds of binding. A claim like
that rots silently: pylint gains a checker, `.pylintrc` gets an extra
option, and the script goes on counting sites that are no longer blind
spots while CLAUDE.md goes on telling people to run both. So
`PylintReallyIsBlindTests` runs the real pylint, with this repository's real
`.pylintrc`, over a fixture holding one of each - and a matching visible
case one line away, to prove the run was actually checking something.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from sim import pylint_blind_spots as blind


class _TempTree(object):
    """A scratch directory of fixture files, scanned as its own root.

    Unlike test_code_health.py's _TempRoot this rebinds nothing global -
    blind_spots() takes its root as an argument - so there is no state to
    restore and nothing that can leave a later test pointed at a deleted
    directory.
    """

    def __init__(self, files):
        self.files = files
        self._dir = None

    def __enter__(self):
        self._dir = tempfile.mkdtemp(prefix="blind_spots_test_")
        for relative_path, content in self.files.items():
            full_path = os.path.join(self._dir, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as handle:
                handle.write(textwrap.dedent(content))
        return self._dir

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self._dir, ignore_errors=True)
        return False


def _names(found, category):
    return sorted(name for _path, _line, name in found.get(category, []))


class ModuleLevelAssignmentTests(unittest.TestCase):

    def test_finds_a_short_module_level_name(self):
        with _TempTree({"a.py": """\
            import os
            KB = os.path.join("a", "b")
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level assignment"), ["KB"])

    def test_ignores_a_spelled_out_module_level_name(self):
        with _TempTree({"a.py": """\
            import os
            KNOWLEDGE_DIR = os.path.join("a", "b")
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level assignment"), [])

    def test_a_short_name_inside_a_function_is_not_a_blind_spot(self):
        """pylint DOES report this one, so counting it here would double-count
        it against the worklist pylint already prints."""
        with _TempTree({"a.py": """\
            def f():
                ab = 1
                return ab
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level assignment"), [])


class ModuleLevelLoopTargetTests(unittest.TestCase):

    def test_finds_a_short_module_level_loop_target(self):
        with _TempTree({"a.py": """\
            for p in [1, 2]:
                print(p)
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level loop target"), ["p"])

    def test_a_function_level_loop_target_is_not_a_blind_spot(self):
        with _TempTree({"a.py": """\
            def f():
                for z in [1]:
                    print(z)
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level loop target"), [])

    def test_ignores_a_spelled_out_loop_target(self):
        with _TempTree({"a.py": """\
            for prereq_id in [1, 2]:
                print(prereq_id)
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level loop target"), [])


class LambdaParameterTests(unittest.TestCase):

    def test_finds_a_short_lambda_parameter_at_module_level(self):
        with _TempTree({"a.py": """\
            sort_key = lambda a: a + 1
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "lambda parameter"), ["a"])

    def test_finds_one_inside_a_function_too(self):
        """A lambda's parameters are invisible to pylint wherever the lambda
        sits, so scope is not part of this detector's question."""
        with _TempTree({"a.py": """\
            def f(items):
                return sorted(items, key=lambda d: d.size)
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "lambda parameter"), ["d"])

    def test_ignores_a_spelled_out_lambda_parameter(self):
        with _TempTree({"a.py": """\
            sort_key = lambda deposit: deposit.grade
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "lambda parameter"), [])


class CountingRuleTests(unittest.TestCase):

    def test_underscores_do_not_buy_length(self):
        """`_k` is two characters of meaning behind a visibility marker."""
        with _TempTree({"a.py": """\
            for _k in [1]:
                print(_k)
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level loop target"), ["_k"])

    def test_the_section_7_exemptions_are_not_counted(self):
        with _TempTree({"a.py": """\
            for i in [1]:
                print(i)
            for x in [1]:
                print(x)
            for y in [1]:
                print(y)
            """}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level loop target"), [])

    def test_a_file_that_does_not_parse_is_skipped_rather_than_fatal(self):
        """One unparseable file in the tree must not stop the scan: the
        answer for the other 196 is still worth having."""
        with _TempTree({"broken.py": "def f(\n",
                        "fine.py": "for p in [1]:\n    print(p)\n"}) as root:
            self.assertEqual(_names(blind.blind_spots(root),
                                    "module-level loop target"), ["p"])


class PylintReallyIsBlindTests(unittest.TestCase):
    """The claim CLAUDE.md section 7 and .pylintrc both rest on."""

    FIXTURE = textwrap.dedent("""\
        import os
        HIDDEN_BY_CALL = os.path.join("a", "b")
        KB = os.path.join("a", "b")
        QQ = 5
        for p in [1, 2]:
            print(p)
        sort_key = lambda a: a + 1
        """)

    def _pylint_messages(self, source):
        with _TempTree({"probe.py": source}) as root:
            completed = subprocess.run(
                [sys.executable, "-m", "pylint",
                 "--rcfile", os.path.join(_REPO_ROOT, ".pylintrc"),
                 os.path.join(root, "probe.py")],
                capture_output=True, text=True, timeout=120)
            return completed.stdout

    def test_pylint_sees_the_literal_constant_but_none_of_the_three(self):
        if importlib.util.find_spec("pylint") is None:
            self.skipTest("pylint not installed")
        output = self._pylint_messages(self.FIXTURE)
        # The control: pylint IS running and IS checking names here.
        self.assertIn('"QQ"', output,
                      "pylint reported nothing at all - the cross-check "
                      "proves nothing unless the visible case is seen:\n" + output)
        # The three blind spots. If any of these starts being reported,
        # pylint_blind_spots.py is counting work pylint already lists, and
        # CLAUDE.md section 7 is telling people to run a script they no
        # longer need.
        for invisible in ('"KB"', '"p"', '"a"'):
            self.assertNotIn(
                invisible, output,
                "pylint now reports %s. The blind spot has closed; update "
                "sim/pylint_blind_spots.py, .pylintrc's header and "
                "CLAUDE.md section 7 together.\n%s" % (invisible, output))

    def test_the_scanner_finds_exactly_what_pylint_missed(self):
        with _TempTree({"probe.py": self.FIXTURE}) as root:
            found = blind.blind_spots(root)
        self.assertEqual(_names(found, "module-level assignment"), ["KB"])
        self.assertEqual(_names(found, "module-level loop target"), ["p"])
        self.assertEqual(_names(found, "lambda parameter"), ["a"])
        # QQ is short but pylint reports it, so the scanner must not:
        # the two counts are meant to be added, not overlapped.
        self.assertNotIn("QQ", _names(found, "module-level assignment"))
