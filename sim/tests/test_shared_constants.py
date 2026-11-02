"""A physical or biological constant that two modules both need is declared once, and copies that stay under other
names agree.

  1. SingleSourceTests - land.py and agriculture.py get their shared values from sim/world/shared_constants.py; the
     values are the same object, and the fallow share and holding multiplier are one fact in two units.
  2. CrossModuleQuantityEquivalenceTests - hand-listed groups of registry names for one physical fact that standalone
     modules each still declare (demand, demography, military logistics); the declared values must agree. A new
     duplicate under a new name is invisible until it is added to the groups.
"""
QUICK_TOPIC = True

import unittest

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


def _registry_values():
    """{name: declared value} once the world modules that declare the grouped quantities are imported."""
    from sim import constants
    from sim.world import demand, demography, military_logistics, shared_constants  # noqa: F401  (declare on import)
    return {name: entry["value"] for name, entry in constants.REGISTRY.items()}


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
        from sim.world import farm_labour
        self.assertIs(self.agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE,
                      farm_labour.REFERENCE_LABOUR_HOURS_PER_HECTARE)
        self.assertEqual(self.land.LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE,
                         farm_labour.REFERENCE_LABOUR_HOURS_PER_HECTARE)

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
        cls.registry = _registry_values()

    def test_registry_is_not_empty(self):
        # Guards this test file's own plumbing, not the project: if the
        # import silently found nothing, every group check below
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


if __name__ == "__main__":
    unittest.main()
