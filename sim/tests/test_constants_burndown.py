"""Guards the two bugs that made `python3 sim/constants.py --burndown` print
"0 numbers declared" while 32 numbers were declared, and (in
`HardcodedHistoricalOutcomeTests`) the separate `hardcoded_outcome`
kind Complaints/36 asked for.

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
import json
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
        # AGAINST TWO CLEAN SUBPROCESSES, NOT THE IN-PROCESS REGISTRY: inside
        # a full suite run, the in-process registry has accumulated every
        # module that any earlier topic happened to import, so comparing
        # against it would measure test execution order rather than the bug
        # this check is written for - the dual-registry one, where this file
        # loads twice, as __main__ and as sim.constants, with the
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
        # BEHAVIOURAL, NOT A SOURCE SCAN, for the second half of this check:
        # a substring match against inspect.getsource(constants._import_
        # declaring_modules) cannot tell a real entry in the tuple from the
        # identical text sitting in a comment - commenting a module out of
        # the tuple while leaving its name in a nearby comment would still
        # pass - and it says nothing about whether the import actually
        # succeeds or the module's declare() calls actually run. The claim
        # this check exists for -
        # "this module's declared numbers make it into the registry the
        # burndown reads" - is directly observable: run
        # _import_declaring_modules() for real, in a clean subprocess (a
        # fresh process, so this is the burndown tool's own view of the
        # registry, not whatever the rest of this test suite happened to
        # import first), and read back which modules' declarations actually
        # landed, using declare()'s own "declared_in" provenance field
        # rather than re-parsing anything.
        #
        # Finding WHICH modules call declare() at all still has to be a
        # source scan: there is no registry to read before a module is
        # imported, so this first half stays a directory walk for
        # "declare(" - a genuine source property, not a stand-in for one.
        world_directory = os.path.join(_REPOSITORY_ROOT, "sim", "world")
        declaring = set()
        for entry in sorted(os.listdir(world_directory)):
            if not entry.endswith(".py") or entry == "__init__.py":
                continue
            with open(os.path.join(world_directory, entry)) as handle:
                if "declare(" in handle.read():
                    declaring.add("sim.world." + entry[:-3])

        script = (
            "import sys, json; sys.path.insert(0, %r)\n"
            "from sim import constants\n"
            "constants._import_declaring_modules()\n"
            "constants._adopt_the_canonical_registry()\n"
            "print(json.dumps(sorted(set(entry['declared_in'] for entry in "
            "constants.REGISTRY.values()))))\n" % _REPOSITORY_ROOT)
        result = subprocess.run([sys.executable, "-c", script],
                                 cwd=_REPOSITORY_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        actually_registered = set(json.loads(result.stdout.strip()))

        missing = sorted(name for name in declaring if name not in actually_registered)
        self.assertEqual(
            missing, [],
            "these sim/world modules call declare() but "
            "_import_declaring_modules() never actually gets their numbers "
            "into the registry (checked by running it for real, not by "
            "reading its source), so they are missing from the burndown: "
            "%s" % ", ".join(missing))


class OneRegistryAcrossBothImportRootsTests(unittest.TestCase):
    """This repository has TWO import roots and sim/constants.py sits in both.

    The engine is imported rooted at `sim/`, so from inside it the file is
    reachable as `constants`. The sim/world/ modules and the test runner are
    rooted at the REPOSITORY, so they reach the same file as `sim.constants`.
    Running it as a script makes a third, `__main__`.

    Each spelling is a separate module object with its own globals, so a
    plain module-level dict gives each one its own empty copy - declarations
    land in one and the report reads another. That is the same bug this
    file's other tests guard, arriving by a different door, and the engine's
    migration to declare() is what opens that door.
    """

    def test_both_spellings_share_one_registry_object(self):
        sys.path.insert(0, _REPOSITORY_ROOT)
        sys.path.insert(0, os.path.join(_REPOSITORY_ROOT, "sim"))
        try:
            import constants as engine_spelling
            from sim import constants as world_spelling
        finally:
            sys.path.remove(os.path.join(_REPOSITORY_ROOT, "sim"))
            sys.path.remove(_REPOSITORY_ROOT)

        # Two module objects is the NORMAL, expected state - the point is not
        # to prevent that (you cannot, with two roots), it is that they must
        # not own two registries.
        self.assertIs(
            engine_spelling.REGISTRY, world_spelling.REGISTRY,
            "`constants` and `sim.constants` have separate REGISTRY objects. "
            "Anything the engine declares is then invisible to the burndown "
            "and the total is quietly too low - see this class's docstring.")

    def test_an_engine_file_can_be_imported_from_outside_the_repository(self):
        # The failure this catches is an engine file written as `from
        # sim.constants import declare`, which works under the test runner's
        # rooting and raises ModuleNotFoundError under the engine's own. The
        # suite alone would not notice; sim/solve_prices.py would break.
        script = ("import sys; sys.path.insert(0, %r); import engine.core; "
                  "print('ok')" % os.path.join(_REPOSITORY_ROOT, "sim"))
        result = subprocess.run([sys.executable, "-c", script],
                                cwd=os.path.dirname(_REPOSITORY_ROOT),
                                capture_output=True, text=True)
        self.assertEqual(
            result.returncode, 0,
            "the engine cannot be imported rooted at sim/ from outside the "
            "repository. An engine module is probably importing something as "
            "`sim.X`; rooted at sim/ the name `sim` does not exist. Use the "
            "bare spelling in engine files.\n%s" % result.stderr[-600:])


class HardcodedHistoricalOutcomeTests(unittest.TestCase):
    """Complaints/36: `temporary_heuristic` conflated two unlike things -
    honest scaffolding CLAUDE.md SS3.1 allows ("no mechanism exists yet"),
    and a hardcoded historical outcome SS3.1 forbids outright ("this IS the
    answer, copied from the record"). `hardcoded_outcome` is the
    kind that separates them.

    Unlike `temporary_heuristic`, which will always have a tail, this kind
    is expected to reach ZERO. These tests guard the mechanism (the kind
    exists, `declare()` accepts it, `--burndown` reports it separately and
    names the zero target) rather than any specific count, so they do not
    become stale as entries are fixed and the count drops.
    """

    def _run_burndown(self):
        result = subprocess.run(
            [sys.executable, os.path.join("sim", "constants.py"), "--burndown"],
            cwd=_REPOSITORY_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout, result.stderr

    def test_hardcoded_outcome_is_a_registered_kind(self):
        sys.path.insert(0, _REPOSITORY_ROOT)
        try:
            from sim import constants
        finally:
            sys.path.remove(_REPOSITORY_ROOT)
        self.assertIn("hardcoded_outcome", constants.KINDS)

    def test_declare_accepts_the_new_kind(self):
        # A clean subprocess, like this file's other declare()-exercising
        # checks, so a throwaway probe constant never pollutes the shared
        # REGISTRY any other test in this process might read.
        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "from sim import constants\n"
            "value = constants.declare(\n"
            "    '_PROBE_HARDCODED_HISTORICAL_OUTCOME', 1.0,\n"
            "    kind='hardcoded_outcome', unit='test',\n"
            "    why='Exercises the new kind end to end; not a real "
            "declaration read by any production code.')\n"
            "print(value)\n" % _REPOSITORY_ROOT)
        result = subprocess.run([sys.executable, "-c", script],
                                cwd=_REPOSITORY_ROOT, capture_output=True,
                                text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "1.0")

    def test_burndown_reports_historical_outcomes_as_their_own_list(self):
        script = (
            "import sys, json; sys.path.insert(0, %r)\n"
            "from sim import constants\n"
            "constants._import_declaring_modules()\n"
            "constants._adopt_the_canonical_registry()\n"
            "result = constants.burndown()\n"
            "print(json.dumps({\n"
            "    'outcome_names': [e['name'] for e in "
            "result['historical_outcomes']],\n"
            "    'heuristic_names': [e['name'] for e in "
            "result['outstanding']],\n"
            "}))\n" % _REPOSITORY_ROOT)
        result = subprocess.run([sys.executable, "-c", script],
                                cwd=_REPOSITORY_ROOT, capture_output=True,
                                text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        # Complaints/36 named these two explicitly. If sim/engine/economy.py
        # is ever dropped from _import_declaring_modules(), or either
        # reclassification is quietly reverted, this fails loudly instead
        # of the count just silently reading zero - the exact failure mode
        # Complaints/36 exists to prevent one level up.
        self.assertIn("DEBT_BASE_RATE", payload["outcome_names"])
        self.assertIn("LIVING_COST_TAX_RATE", payload["outcome_names"])
        # And they must not ALSO count as temporary_heuristic - one entry,
        # one kind, which is the whole point of separating the bucket.
        self.assertNotIn("DEBT_BASE_RATE", payload["heuristic_names"])
        self.assertNotIn("LIVING_COST_TAX_RATE", payload["heuristic_names"])

    def test_cli_burndown_names_the_kind_and_states_the_zero_target(self):
        stdout, _stderr = self._run_burndown()
        self.assertIn("HARDCODED OUTCOME", stdout)
        self.assertIn("ZERO", stdout)
        self.assertIn("DEBT_BASE_RATE", stdout)
        self.assertIn("LIVING_COST_TAX_RATE", stdout)

    def test_cli_still_reports_declared_count_first(self):
        # The new, loud section must not break the existing contract this
        # file's OTHER tests (and anyone scripting the tool) rely on: the
        # first line of stdout is still "<N> numbers declared, ...", with
        # N as the first whitespace-separated token.
        stdout, _stderr = self._run_burndown()
        first_line = stdout.splitlines()[0]
        self.assertIn("numbers declared", first_line)
        declared = int(stdout.split()[0])
        self.assertGreater(declared, 0)


if __name__ == "__main__":
    unittest.main()
