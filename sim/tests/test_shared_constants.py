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
     exactly the check that would have caught the LAND_LABOUR_OUTPUT_
     ELASTICITY / LABOUR_OUTPUT_ELASTICITY split before this task existed,
     had someone written it down at the time.
  3. UndeclaredLiteralDuplicateTests - the case that does not even show up
     in the declare() registry: sim/world/labour_market.py's own __main__
     demo block uses the reference labour-hours-per-hectare figure twice as
     a bare `150.0` literal rather than a declared name. Not something
     declare()'s own same-name/different-value check can ever see, since
     an undeclared literal carries no name to collide on.

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
    """The one case that never reaches the declare() registry at all:
    sim/world/labour_market.py's own __main__ demo block uses
    REFERENCE_LABOUR_HOURS_PER_HECTARE's value twice as a bare `150.0`
    literal, not a declared name. This cannot be structurally fixed from
    outside labour_market.py (out of this task's ownership - see the
    task's own report), so this test only keeps the two known sites honest:
    if either literal is ever changed without noticing it is the same
    physical figure land.py and agriculture.py now share, this fails.

    A source-text regex is a poor substitute for an import-time check and
    is deliberately narrow: it names the exact two lines found when this
    test was written and fails loudly, with an explanatory message, if
    neither pattern is found any more (the code moved and this test needs
    updating) rather than silently passing on zero matches.
    """

    def test_labour_market_demo_literals_still_match_the_shared_constant(self):
        from sim.world import shared_constants
        path = os.path.join(_REPOSITORY_ROOT, "sim", "world", "labour_market.py")
        with open(path) as handle:
            source = handle.read()
        patterns = [
            r"reference_hours\s*=\s*([\d_]+\.\d+)\s*\*\s*10_000\.0",
            r"grown_hours\s*=\s*([\d_]+\.\d+)\s*\*\s*grown_land\.hectares",
        ]
        found_any = False
        for pattern in patterns:
            match = re.search(pattern, source)
            if match is None:
                continue
            found_any = True
            literal_value = float(match.group(1).replace("_", ""))
            self.assertEqual(
                literal_value, shared_constants.REFERENCE_LABOUR_HOURS_PER_HECTARE,
                "sim/world/labour_market.py's own %r no longer matches "
                "sim/world/shared_constants.REFERENCE_LABOUR_HOURS_PER_"
                "HECTARE (%.4g) - the same reference labour-per-hectare "
                "figure land.py and agriculture.py now share a single "
                "declaration for is still a bare, undeclared literal here, "
                "and it has drifted."
                % (pattern, shared_constants.REFERENCE_LABOUR_HOURS_PER_HECTARE))
        if not found_any:
            self.fail(
                "neither known bare-150.0-literal site in "
                "sim/world/labour_market.py's __main__ demo block matched "
                "any more - the code moved. This is not a failure of the "
                "duplication itself; update this test's patterns (or drop "
                "this check if the literal was declared or removed).")


if __name__ == "__main__":
    unittest.main()
