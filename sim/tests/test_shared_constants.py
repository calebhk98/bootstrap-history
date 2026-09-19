"""Guards the duplication class this task exists for: a physical or
biological constant declared more than once, under the same name or a
different one, with nothing keeping the copies equal.

THE INCIDENT. `sim/world/land.py` needed `sim/world/agriculture.py`'s own
Cobb-Douglas labour-intensity physics (the labour output elasticity and the
reference labour-hours-per-hectare figure it is calibrated against) but is
STANDALONE by design and may not import `agriculture.py` - so it duplicated
the numbers instead, under its own `LAND_`-prefixed names. Nothing failed
when the two definitions were created; nothing would have failed if they
had later drifted apart, either import path stays syntactically and
semantically valid on its own. `sim/world/shared_constants.py` gives the
shared facts ONE declaration; this file is the guard that makes a second,
independent copy - of a name already migrated, or of a genuinely new
quantity - visible instead of silent.

THREE LAYERS, EACH CATCHING A DIFFERENT SHAPE OF THE SAME MISTAKE.

  1. SingleSourceTests - the specific fix. land.py and agriculture.py now
     both get these six values from one declaration; this asserts they are
     literally the same value (not merely equal by coincidence) and proves
     the FALLOW hard case (a different name AND a different unit for the
     same fact) is now correct arithmetic on one shared number rather than
     two independently-set ones.
  2. CrossModuleQuantityEquivalenceTests - the general net for quantities
     this task did NOT migrate (sim/world/demand.py, sim/world/demography.py
     and sim/world/military_logistics.py each still declare their own copy
     of the human-calorie and grain-energy figures, deliberately, to stay
     standalone - see shared_constants.py's own WHAT DOES NOT BELONG HERE).
     Explicit, hand-maintained equivalence groups of registry names known
     to describe the same physical fact; asserts they still agree. THIS IS
     WHERE A REAL DUPLICATE THAT NOBODY MIGRATES WOULD BE CAUGHT, and
     exactly the kind of check that would have caught the LAND_LABOUR_OUTPUT_
     ELASTICITY / LABOUR_OUTPUT_ELASTICITY split before this task existed,
     had it been written down.
  3. UndeclaredLiteralDuplicateTests - the case that does not even show up
     in the declare() registry, because an undeclared literal carries no
     name to collide on. sim/world/labour_market.py's own __main__ demo
     block wrote the reference labour-hours-per-hectare figure out twice as
     a bare `150.0` rather than reading the declared name. It now imports
     the declaration, so these tests assert that no such copy exists at
     all, rather than merely keeping two known copies honest. The
     recurrence half is the one that earns its place - no float anywhere in
     that file may equal the shared constant's value - because it catches a
     fifth copy under any name, not only at the two sites somebody thought
     to list. See that class's own docstring for why it changed.

WHAT THIS DOES NOT CATCH, STATED PLAINLY. A BRAND NEW duplicate - a
constant some future module declares under a name not yet listed in
_EQUIVALENCE_GROUPS below, describing a quantity none of these tests know
to compare - is invisible to all three layers until a human or agent
notices the semantic overlap and adds it to the list. There is no
mechanical way to tell that two arbitrarily-named floats mean the same
physical thing; `declare()`'s own registry already catches the easy half of
this problem for free (the SAME name with a DIFFERENT value fails loudly at
import time, project-wide, with no test needed) - what remains, and what
this file's equivalence groups exist for, is the hard half: the SAME
quantity under a DIFFERENT name, which is exactly what land.py and
agriculture.py had.
"""
import ast
import os
import re
import subprocess
import sys
import unittest

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# Registry names known to describe the SAME physical or biological quantity
# under DIFFERENT names, across modules this task did not migrate (see the
# module docstring). Each inner tuple is one such group; every name in a
# group must resolve to the same declared value once the modules that
# declare it are imported. Add to this list the day another such pair is
# found - that is the whole maintenance cost of this check, and it is a
# permanent, growing job, exactly like the naming sweep CLAUDE.md SS7
# describes for a different kind of duplication.
_EQUIVALENCE_GROUPS = (
    ("SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY",  # shared_constants
     "HUMAN_SUBSISTENCE_CALORIES_PER_CAPITA_DAY",          # demand.py
     "SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY",      # demography.py
     "SEDENTARY_ENERGY_REQUIREMENT_KCAL_PER_DAY"),         # military_logistics.py
    ("WHEAT_ENERGY_KCAL_PER_KG",                           # shared_constants, demand.py
     "GRAIN_ENERGY_KCAL_PER_KG"),                          # military_logistics.py
)


def _registry_after_importing_declaring_modules():
    """The declare() REGISTRY, in a clean subprocess, after every module
    that calls declare() has been imported - the same two-step
    sim/tests/test_constants_burndown.py already uses (import, then adopt
    the canonical copy), run here to fetch VALUES rather than a count.
    """
    script = (
        "import json, sys; sys.path.insert(0, %r)\n"
        "from sim import constants\n"
        "constants._import_declaring_modules()\n"
        "constants._adopt_the_canonical_registry()\n"
        "print(json.dumps({name: entry['value']\n"
        "                   for name, entry in constants.REGISTRY.items()}))\n"
        % _REPOSITORY_ROOT)
    result = subprocess.run([sys.executable, "-c", script],
                            cwd=_REPOSITORY_ROOT, capture_output=True,
                            text=True)
    if result.returncode != 0:
        raise AssertionError(
            "could not import the declaring modules in a clean subprocess: "
            "%s" % result.stderr)
    import json
    return json.loads(result.stdout.strip())


class SingleSourceTests(unittest.TestCase):
    """land.py and agriculture.py both get these values from ONE
    declaration in sim/world/shared_constants.py now - not merely equal
    values, the SAME value, so there is structurally no way for the two
    modules' own public names to disagree with each other any more.
    """

    @classmethod
    def setUpClass(cls):
        from sim.world import agriculture, land, shared_constants
        cls.agriculture = agriculture
        cls.land = land
        cls.shared = shared_constants

    def test_reference_labour_hours_per_hectare_is_one_value(self):
        self.assertIs(self.agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE,
                      self.shared.REFERENCE_LABOUR_HOURS_PER_HECTARE)
        self.assertEqual(self.land.LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE,
                         self.shared.REFERENCE_LABOUR_HOURS_PER_HECTARE)

    def test_labour_output_elasticity_is_one_value(self):
        self.assertIs(self.agriculture.LABOUR_OUTPUT_ELASTICITY,
                      self.shared.LABOUR_OUTPUT_ELASTICITY)
        self.assertEqual(self.land.LAND_LABOUR_OUTPUT_ELASTICITY,
                         self.shared.LABOUR_OUTPUT_ELASTICITY)

    def test_annual_labour_hours_per_farm_worker_is_one_value(self):
        self.assertIs(self.agriculture.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER,
                      self.shared.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER)
        self.assertEqual(
            self.land.LAND_ANNUAL_LABOUR_HOURS_PER_FARM_WORKER,
            self.shared.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER)

    def test_subsistence_energy_requirement_is_one_value(self):
        self.assertEqual(
            self.agriculture.HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY,
            self.shared.SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY)
        self.assertEqual(
            self.land.LAND_HUMAN_CALORIC_NEED_KCAL_PER_DAY,
            self.shared.SUBSISTENCE_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY)

    def test_wheat_energy_kcal_per_kg_is_one_value(self):
        self.assertIs(self.agriculture.WHEAT_ENERGY_KCAL_PER_KG,
                      self.shared.WHEAT_ENERGY_KCAL_PER_KG)
        self.assertIs(self.land.WHEAT_ENERGY_KCAL_PER_KG,
                      self.shared.WHEAT_ENERGY_KCAL_PER_KG)

    def test_fallow_hard_case_is_derived_not_duplicated(self):
        # THE HARD CASE: land.py's FALLOW_HOLDING_MULTIPLIER (holding
        # hectares per cropped hectare) and agriculture.py's
        # FALLOW_SHARE_OF_HOLDING (fraction of a holding idle) are the SAME
        # physical fact under a DIFFERENT name and a DIFFERENT unit. This
        # asserts the exact algebraic relationship, computed from the one
        # shared declaration, rather than merely checking two independently
        # -set numbers still happen to agree.
        self.assertEqual(
            self.agriculture.FALLOW_SHARE_OF_HOLDING,
            self.shared.FALLOW_SHARE_OF_HOLDING)
        expected_multiplier = 1.0 / (1.0 - self.shared.FALLOW_SHARE_OF_HOLDING)
        self.assertAlmostEqual(
            self.land.FALLOW_HOLDING_MULTIPLIER, expected_multiplier, places=12)
        # And the historical value (a 50/50 two-field split) is unchanged -
        # this is a refactor, not a physics change.
        self.assertAlmostEqual(self.land.FALLOW_HOLDING_MULTIPLIER, 2.0,
                               places=12)

    def test_shared_constants_module_imports_nothing_but_the_registry(self):
        # The property that makes sharing these constants safe for two
        # STANDALONE modules to depend on: sim/world/shared_constants.py
        # must not import land.py, agriculture.py, or any other sim/world/
        # module, or importing it would recreate exactly the concurrent-
        # edit exposure the STANDALONE rule exists to prevent.
        import ast
        path = os.path.join(_REPOSITORY_ROOT, "sim", "world",
                            "shared_constants.py")
        with open(path) as handle:
            source = handle.read()
        # AST, not a text scan: this module's own docstring quotes import
        # lines in prose (explaining what NOT to do), and a plain
        # line-prefix match would count those as real imports.
        tree = ast.parse(source, filename=path)
        imports_found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = ", ".join(alias.name for alias in node.names)
                imports_found.append("from %s import %s" % (node.module, names))
            elif isinstance(node, ast.Import):
                imports_found.append(
                    "import " + ", ".join(alias.name for alias in node.names))
        self.assertEqual(
            imports_found, ["from sim.constants import declare"],
            "sim/world/shared_constants.py imports something other than "
            "the declare() registry: %r. A shared-constants module that "
            "imports another domain module reintroduces the concurrent-"
            "edit coupling STANDALONE sim/world/ modules are built to "
            "avoid." % (imports_found,))


class CrossModuleQuantityEquivalenceTests(unittest.TestCase):
    """The general net: quantities this task did not migrate, checked by
    explicit, hand-maintained equivalence group (see the module docstring
    and _EQUIVALENCE_GROUPS above). Catches a future edit that changes one
    module's own copy of a shared fact without updating the others - the
    exact recurrence this task was asked to make impossible for the two
    constants it DID migrate, and merely detectable (not yet prevented) for
    the ones it did not.
    """

    @classmethod
    def setUpClass(cls):
        cls.registry = _registry_after_importing_declaring_modules()

    def test_registry_is_not_empty(self):
        # Guards this test file's own plumbing, not the project: if the
        # subprocess import silently found nothing, every group check below
        # would vacuously pass by finding no names to compare, which is a
        # worse failure than a slow test.
        self.assertGreater(len(self.registry), 0)

    def test_equivalence_groups_agree(self):
        failures = []
        for group in _EQUIVALENCE_GROUPS:
            present = {name: self.registry[name] for name in group
                      if name in self.registry}
            missing = [name for name in group if name not in self.registry]
            if missing:
                failures.append(
                    "group %s: %s not found in the registry at all (moved, "
                    "renamed, or the declaring module failed to import - "
                    "update this test's _EQUIVALENCE_GROUPS either way)"
                    % (group, missing))
                continue
            values = set(present.values())
            if len(values) > 1:
                failures.append(
                    "group %s no longer agrees: %s - one of these was "
                    "changed without updating the others. If the change "
                    "was deliberate, the same physical quantity now has "
                    "two different values under two different names, "
                    "which is the exact bug this file exists to catch."
                    % (group, present))
        self.assertEqual(failures, [], "\n".join(failures))


class UndeclaredLiteralDuplicateTests(unittest.TestCase):
    """The fourth copy of the reference labour intensity, now closed.

    NOT A SOURCE-TEXT CHECK ON A LITERAL, A STRUCTURAL ONE ON RECURRENCE.
    When land.py and agriculture.py were gathered onto one declaration of
    REFERENCE_LABOUR_HOURS_PER_HECTARE, sim/world/labour_market.py's own
    __main__ demo was found writing the same physical figure out twice as a
    bare `150.0`, outside that gathering change's ownership. The demo now
    imports the shared constant, so this asks the stronger question a
    source-text match on a bare `150.0` could not: not "does the duplicate
    still hold the right value", but "can the duplicate come back". Two
    assertions, both structural rather than textual:

      1. The demo's two hours figures are each computed FROM the shared
         name, checked on the parsed syntax tree so that a comment or a
         string mentioning the name cannot satisfy it.
      2. No float anywhere in labour_market.py equals the shared constant's
         value. This is the half that actually prevents recurrence: it
         fails on a fifth copy appearing anywhere in the file, under any
         variable name, not only at the two sites somebody thought to list.

    Assertion 2 compares against the constant's live value rather than
    against a hardcoded 150.0, so changing the declaration re-aims the test
    instead of breaking it.
    """

    _LABOUR_MARKET_PATH = os.path.join(
        _REPOSITORY_ROOT, "sim", "world", "labour_market.py")
    _SHARED_NAME = "REFERENCE_LABOUR_HOURS_PER_HECTARE"

    def _parsed_labour_market(self):
        with open(self._LABOUR_MARKET_PATH) as handle:
            return ast.parse(handle.read(), filename=self._LABOUR_MARKET_PATH)

    def test_the_demo_computes_both_hours_figures_from_the_shared_name(self):
        """The two sites that held the bare literal now read the declaration.

        Walks every assignment in the file looking for the two target
        names, then checks the shared name appears in that assignment's own
        value expression. A `getsource`-style substring search over the
        whole file would pass on this very docstring, which names the
        constant three times.
        """
        wanted = {"reference_hours", "grown_hours"}
        seen = {}
        for node in ast.walk(self._parsed_labour_market()):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in wanted:
                    names_used = {inner.id for inner in ast.walk(node.value)
                                  if isinstance(inner, ast.Name)}
                    seen[target.id] = names_used
        missing = sorted(wanted - set(seen))
        self.assertEqual(
            missing, [],
            "sim/world/labour_market.py's demo no longer assigns %s - the "
            "code moved, so this check is no longer looking at the thing it "
            "was written about. Re-aim it rather than deleting it: the "
            "property is that the demo's labour-hours figures come from "
            "shared_constants, however they are spelled." % missing)
        for target_name, names_used in sorted(seen.items()):
            self.assertIn(
                self._SHARED_NAME, names_used,
                "sim/world/labour_market.py's demo computes %r without "
                "reading %s. That is how the bare 150.0 got here the first "
                "time: the same physical figure written out by hand in a "
                "fourth place, free to drift away from the three that share "
                "a declaration." % (target_name, self._SHARED_NAME))

    def test_no_bare_literal_of_that_value_remains_anywhere_in_the_file(self):
        """The recurrence guard.

        Any float in the file equal to the shared constant's value is a
        fresh undeclared copy, wherever it is and whatever it is called.
        Checked against the live declaration, so moving the declared value
        re-aims this test instead of breaking it.
        """
        from sim.world import shared_constants
        expected = getattr(shared_constants, self._SHARED_NAME)
        offenders = []
        for node in ast.walk(self._parsed_labour_market()):
            if (isinstance(node, ast.Constant)
                    and isinstance(node.value, float)
                    and node.value == expected):
                offenders.append(node.lineno)
        self.assertEqual(
            offenders, [],
            "sim/world/labour_market.py writes %.4g as a bare literal at "
            "line(s) %s. That is %s's value, and land.py, agriculture.py "
            "and this module's own demo all reach it through the one "
            "declaration in sim/world/shared_constants.py. A fourth "
            "hand-written copy is exactly what this file exists to stop: "
            "import the name instead."
            % (expected, offenders, self._SHARED_NAME))


if __name__ == "__main__":
    unittest.main()
