"""Complaint 285: the unit registry decides which reply keys are quantities and which dimension a key has, so a reply
converts them to the player's units. No game is built."""

QUICK_TOPIC = True

import unittest

from sim.engine import units as U


class UnitRegistryRules(unittest.TestCase):
    def setUp(self):
        U.set_registry(None)
        self.registry = U.registry()

    def test_a_temperature_key_matches_the_temperature_field_rule(self):
        self.assertEqual(U.field_rule(self.registry, "furnace_temperature_c")["dimension"], "temperature")

    def test_the_detector_reads_the_registry_not_a_private_list(self):
        self.assertTrue(U.looks_like_quantity(self.registry, "annual_wage_bill"))
        self.assertFalse(U.looks_like_quantity(self.registry, "price_index"))
        self.assertFalse(U.looks_like_quantity(self.registry, "population"))


if __name__ == "__main__":
    unittest.main()
