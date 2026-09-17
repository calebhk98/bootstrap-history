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

    def test_a_clean_registry_matches_the_tools_count(self):
        # WHAT THIS REPLACES, AND WHY. The first version of this check
        # compared an IN-PROCESS registry against the tool's. That was wrong
        # and it failed as soon as two new declaring modules appeared: inside
        # a full suite run the in-process registry has accumulated every
        # module that any earlier topic happened to import, so it counts more
        # than the tool's explicit list does. The check was measuring test
        # execution order, not the bug it was written for.
        #
        # The bug it IS written for is the dual-registry one - this file
        # loaded twice, as __main__ and as sim.constants, with the
        # declarations landing in one copy and the report reading the other.
        # Two clean subprocesses catch that without either being polluted:
        # one imports the modules by their dotted names and reads the
        # registry, the other runs the command-line tool.
        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "from sim import constants\n"
            "constants._import_declaring_modules()\n"
            "constants._adopt_the_canonical_registry()\n"
            "print(constants.burndown()['declared'])\n" % _REPOSITORY_ROOT)
        result = subprocess.run([sys.executable, "-c", script],
                                cwd=_REPOSITORY_ROOT, capture_output=True,
                                text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        imported_cleanly = int(result.stdout.strip())

        stdout, _stderr = self._run_burndown()
        from_the_tool = int(stdout.split()[0])
        self.assertEqual(
            imported_cleanly, from_the_tool,
            "importing the declaring modules by name gives a different "
            "count than the command-line tool reports. That is the "
            "two-module-object problem back again - see this module's "
            "docstring.")

    def test_every_declaring_module_under_sim_world_is_in_the_list(self):
        # The rule the comment in _import_declaring_modules() states, now
        # enforced instead of merely asked for. A module that calls declare()
        # and is not in that list has its numbers silently missing from the
        # burndown, which looks exactly like having fewer outstanding
        # promises than you really do - the optimistic direction, and the
        # one nobody checks.
        #
        # This is how transport.py and military_logistics.py went missing:
        # both were written by agents who were correctly told not to edit
        # sim/constants.py, so neither could add itself. A rule that depends
        # on the person who cannot follow it is not a rule.
        world_directory = os.path.join(_REPOSITORY_ROOT, "sim", "world")
        declaring = set()
        for entry in sorted(os.listdir(world_directory)):
            if not entry.endswith(".py") or entry == "__init__.py":
                continue
            with open(os.path.join(world_directory, entry)) as handle:
                if "declare(" in handle.read():
                    declaring.add("sim.world." + entry[:-3])

        sys.path.insert(0, _REPOSITORY_ROOT)
        try:
            import inspect
            from sim import constants
            listed = inspect.getsource(constants._import_declaring_modules)
        finally:
            sys.path.remove(_REPOSITORY_ROOT)

        missing = sorted(name for name in declaring if name not in listed)
        self.assertEqual(
            missing, [],
            "these sim/world modules call declare() but are not in "
            "sim/constants.py's _import_declaring_modules() list, so their "
            "numbers are missing from the burndown: %s" % ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
