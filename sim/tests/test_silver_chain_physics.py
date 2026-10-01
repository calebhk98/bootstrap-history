"""The silver chain in data/production/ agrees with the physics of the
deposits and of the lead it is cupelled from."""
import unittest

from sim.engine.prices import _default_production_entries
from sim.world import deposits
from sim.unit_conversions import KILOGRAMS_PER_TONNE

# PbO + C -> Pb + CO, from molar masses (g/mol).
LEAD_OXIDE_PER_LEAD = (207.2 + 16.0) / 207.2
CARBON_PER_LEAD_OXIDE = 12.011 / (207.2 + 16.0)
CHARCOAL_CARBON_FRACTION = 0.85
FURNACE_FUEL_PER_STOICHIOMETRIC_CARBON = 4.0


def _silver_deposits():
    pool = deposits.load_deposits("silver")
    total = sum(deposit.quantity_tonnes_per_year for deposit in pool)
    return [(deposit, deposit.quantity_tonnes_per_year / total) for deposit in pool]


class SilverChainPhysics(unittest.TestCase):

    def test_litharge_goes_back_through_the_reduction_furnace(self):
        entry = _default_production_entries()["lead_kg"]
        per_kilogram_lead = entry["inputs"]["charcoal_kg"] / entry["outputs"]["lead_kg"]
        one_reduction = (LEAD_OXIDE_PER_LEAD * CARBON_PER_LEAD_OXIDE
                         / CHARCOAL_CARBON_FRACTION)
        # Ore is reduced once and the cupellation litharge a second time.
        self.assertGreaterEqual(
            per_kilogram_lead, 2 * FURNACE_FUEL_PER_STOICHIOMETRIC_CARBON * one_reduction)
        self.assertGreaterEqual(entry["labour_hours"]["furnaceman"], 100.0)

    def test_silver_ore_grade_is_the_deposits_grade(self):
        entry = _default_production_entries()["silver_kg"]
        ore_per_kilogram = entry["inputs"]["silver_ore_kg"] / entry["outputs"]["silver_kg"]
        grade = sum(weight * deposit.ore_grade_kg_per_tonne
                    for deposit, weight in _silver_deposits()) / KILOGRAMS_PER_TONNE
        implied_recovery = 1.0 / (ore_per_kilogram * grade)
        self.assertGreater(implied_recovery, 0.6)
        self.assertLess(implied_recovery, 0.9)

    def test_silver_ore_labour_is_the_deposits_labour_per_tonne_of_rock(self):
        entry = _default_production_entries()["silver_ore_kg"]
        recipe_hours = sum(entry["labour_hours"].values())
        deposit_hours = sum(
            weight * deposits.extraction_cost_labour_hours_per_kg(deposit)
            * deposit.ore_grade_kg_per_tonne for deposit, weight in _silver_deposits())
        self.assertAlmostEqual(recipe_hours / deposit_hours, 1.0, delta=0.1)

    def test_silver_per_lead_is_what_the_argentiferous_deposits_carry(self):
        entry = _default_production_entries()["lead_kg"]
        recipe_silver_per_lead = entry["outputs"]["silver_kg"] / entry["outputs"]["lead_kg"]
        lead_total = 0.0
        silver_total = 0.0
        for deposit in deposits.load_deposits("lead"):
            joint = deposits.joint_output_quantities_kg(deposit)
            if "silver_kg" in joint:
                lead_total += joint["lead_kg"]
                silver_total += joint["silver_kg"]
        self.assertGreater(lead_total, 0.0)
        self.assertAlmostEqual(recipe_silver_per_lead / (silver_total / lead_total), 1.0, delta=0.02)


if __name__ == "__main__":
    unittest.main()
