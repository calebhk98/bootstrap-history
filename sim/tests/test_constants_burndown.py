"""Guards the two bugs that made `python3 sim/constants.py --burndown` print
"0 numbers declared" while 32 numbers were declared.

Milestone 1 in docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md is
"provenance and a burndown". The mechanism was built and then the scoreboard
read zero for its whole life, so nothing could tell progress from no
progress. Both causes were silent:

1. `_import_declaring_modules()` listed only `engine.data`, which declares
   nothing at all, so no module that actually calls declare() was ever
   imported.
2. Running the file as `__main__` loads it a second time under the name
   `sim.constants` when the imported modules do `from sim.constants import
   declare`. Two module objects, two REGISTRY dicts. The declarations landed
   in one and the report read the other.

Neither produced a traceback, and zero was the right answer on the day the
tool was written, which is what made it believable afterwards. These checks
fail if either returns.

unittest.TestCase style, like test_agriculture.py and test_demography.py, so
it can exercise the tool in a subprocess without dragging in the engine.
"""
import os
import subprocess
import sys
import unittest

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


class BurndownActuallyCountsTests(unittest.TestCase):

    def _run_burndown(self):
        result = subprocess.run(
            [sys.executable, os.path.join("sim", "constants.py"), "--burndown"],
            cwd=_REPOSITORY_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout, result.stderr

    def test_the_burndown_does_not_report_zero_declared(self):
        # The single check that would have caught both bugs. It asserts a
        # lower bound rather than an exact count, so adding constants does
        # not fail it - what must never happen again is the tool reporting
        # nothing while modules are declaring.
        stdout, _stderr = self._run_burndown()
        declared = int(stdout.split()[0])
        self.assertGreater(
            declared, 0,
            "sim/constants.py --burndown reports zero declared numbers. "
            "Either _import_declaring_modules() is missing a module that "
            "calls declare(), or this file is being loaded twice (as "
            "__main__ and as sim.constants) and the report is reading the "
            "wrong REGISTRY. See this module's docstring.")

    def test_no_declaring_module_fails_to_import(self):
        # The first bug hid behind a stderr line nobody read. If a module in
        # the list cannot be imported its numbers silently vanish from the
        # count, which looks exactly like progress.
        _stdout, stderr = self._run_burndown()
        self.assertNotIn(
            "could not import", stderr,
            "a module listed in _import_declaring_modules() failed to "
            "import, so its declared numbers are missing from the burndown "
            "and the total is quietly too low.")

    def test_the_world_modules_constants_are_actually_counted(self):
        # Specific rather than general on purpose: sim/world/ is where the
        # constants currently live, and an import list that drops it is the
        # exact bug this file exists for.
        stdout, _stderr = self._run_burndown()
        self.assertIn("sim.world.agriculture", stdout)
        self.assertIn("sim.world.demography", stdout)

    def test_in_process_and_subprocess_agree(self):
        # The dual-registry bug made these two disagree: importing the
        # modules by hand showed 32, running the tool showed 0. If they ever
        # disagree again, the two-module-object problem is back.
        sys.path.insert(0, _REPOSITORY_ROOT)
        try:
            from sim.world import agriculture as _agriculture  # noqa: F401
            from sim.world import demography as _demography    # noqa: F401
            from sim import constants
            in_process = constants.burndown()["declared"]
        finally:
            sys.path.remove(_REPOSITORY_ROOT)

        stdout, _stderr = self._run_burndown()
        from_the_tool = int(stdout.split()[0])
        self.assertEqual(
            in_process, from_the_tool,
            "the registry seen by an in-process import disagrees with the "
            "one the command-line tool reports - see this module's "
            "docstring on the two module objects.")


if __name__ == "__main__":
    unittest.main()
