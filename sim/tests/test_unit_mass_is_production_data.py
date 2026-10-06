"""Complaints/399: a good's unit mass can be stated in its production entry, and the validator checks it."""

QUICK_TOPIC = True

import copy
import unittest

from sim.economy import good_mass
from sim.engine import validate_production
from sim.world import demand


class StatedUnitMass(unittest.TestCase):

    def test_stated_masses_beat_the_inferred_ones(self):
        production = demand.production_data()
        self.assertEqual(good_mass.unit_mass_and_source("stone_blocks", production),
                         (140.0, good_mass.SOURCE_STATED))
        self.assertEqual(good_mass.unit_mass_and_source("brick_1000", production),
                         (2500.0, good_mass.SOURCE_STATED))
        mass, source = good_mass.unit_mass_and_source("parchment_sheet", production)
        self.assertLess(mass, 0.1)
        self.assertEqual(source, good_mass.SOURCE_STATED)

    def test_a_good_without_a_stated_mass_is_inferred_as_before(self):
        self.assertEqual(good_mass.unit_mass_and_source("wheat_kg", {})[1], good_mass.SOURCE_MASS_UNIT)

    def test_the_validator_rejects_a_bad_or_misplaced_mass(self):
        entry = copy.deepcopy(demand.production_data()["stone_blocks"])
        self.assertEqual(validate_production.check_unit_mass("stone_blocks", entry), [])
        for bad in (0, -3, "heavy", True, float("inf")):
            entry["unit_mass_kg"] = bad
            self.assertTrue(validate_production.check_unit_mass("stone_blocks", entry), bad)
        entry["unit_mass_kg"] = 5.0
        self.assertTrue(validate_production.check_unit_mass("another_good", entry))


if __name__ == "__main__":
    unittest.main()
