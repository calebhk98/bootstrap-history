"""A society that cannot hold an animal must not make it, and a household's own plot is land, not a mine."""

QUICK_TOPIC = True

import unittest

from sim.economy import households_own, recipes
from sim.engine import validate_production


def entry(extracted_from, **fields):
    return {"outputs": {"thing": 1.0}, "labour_hours": {"hand": 1.0}, "land_hectare_years": 0.01, "extracted_from": extracted_from, **fields}


class AnimalGateTests(unittest.TestCase):
    PACK_ANIMAL = {"serves": {"animal": "mule"}, "days_per_year": 150.0}

    def test_a_carrier_animal_with_no_gate_is_a_problem(self):
        problems = validate_production.check_animal_gate("mule", {"carrier_use": self.PACK_ANIMAL, "requires_node": None})
        self.assertEqual(len(problems), 1)

    def test_a_carrier_animal_with_no_requires_field_is_a_problem(self):
        self.assertEqual(len(validate_production.check_animal_gate("mule", {"carrier_use": self.PACK_ANIMAL})), 1)

    def test_a_gated_carrier_animal_is_fine(self):
        self.assertEqual(validate_production.check_animal_gate(
            "mule", {"carrier_use": self.PACK_ANIMAL, "requires_node": "lnd_mule_transport"}), [])

    def test_a_vehicle_with_no_gate_is_not_an_animal(self):
        self.assertEqual(validate_production.check_animal_gate(
            "cart", {"carrier_use": {"serves": {"model": "pack"}, "days_per_year": 150.0}, "requires_node": None}), [])


class OwnPlotIsLandTests(unittest.TestCase):
    def recipe(self, extracted_from):
        return recipes.recipe_from_entry("thing", entry(extracted_from))

    def test_a_coal_seam_is_not_a_household_plot(self):
        recipe = self.recipe("coal seam")
        self.assertFalse(households_own.is_own_plot_recipe("thing", recipe, {"thing": 0.01}))

    def test_arable_land_is_a_household_plot(self):
        recipe = self.recipe("arable land")
        self.assertTrue(households_own.is_own_plot_recipe("thing", recipe, {"thing": 0.01}))

    def test_standing_timber_is_a_household_plot(self):
        recipe = self.recipe("standing timber")
        self.assertTrue(households_own.is_own_plot_recipe("thing", recipe, {"thing": 0.01}))


if __name__ == "__main__":
    unittest.main()
