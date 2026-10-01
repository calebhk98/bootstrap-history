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
# Recoveries stated in the lead recipe's own yield_basis.
LEAD_SMELTING_RECOVERY = 0.87
SILVER_TO_BULLION_RECOVERY = 0.90
CUPELLATION_SILVER_RECOVERY = 0.92
# 2 Pb + O2 -> 2 PbO, from molar masses.
OXYGEN_PER_LEAD = 0.5 * 32.0 / 207.2
LEAD_PER_TONNE_KG = 1000.0
OXYGEN_MASS_FRACTION_OF_AIR = 0.232
AIR_KG_PER_CUBIC_METRE = 1.2
# Labelled heuristics (conf D): bellows air is mostly wasted on the bath, one
# hand bellows moves tens of cubic metres an hour, a test holds about a
# hundred kilograms of bullion per shift, hand cobbing and washing take at
# least about ten hours per tonne of rock.
BLAST_EXCESS_OVER_STOICHIOMETRY = 10.0
BELLOWS_CUBIC_METRES_PER_HOUR = 60.0
BULLION_PER_CUPEL_SHIFT_KG = 100.0
HOURS_PER_SHIFT = 8.0
HAND_DRESSING_HOURS_PER_TONNE_OF_ROCK_FLOOR = 10.0


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

    def test_silver_per_lead_is_the_assay_mean_times_the_recoveries(self):
        entry = _default_production_entries()["lead_kg"]
        recipe_silver_per_lead = entry["outputs"]["silver_kg"] / entry["outputs"]["lead_kg"]
        lead_total = 0.0
        silver_total = 0.0
        for deposit in deposits.load_deposits("lead"):
            joint = deposits.joint_output_quantities_kg(deposit)
            lead_total += joint["lead_kg"]
            silver_total += joint.get("silver_kg", 0.0)
        self.assertGreater(silver_total, 0.0)
        # Silver follows the lead into the bullion, then cupellation keeps most of it.
        recovered = silver_total / lead_total * SILVER_TO_BULLION_RECOVERY * CUPELLATION_SILVER_RECOVERY
        self.assertAlmostEqual(recipe_silver_per_lead / recovered, 1.0, delta=0.02)

    def test_a_lead_deposit_carries_the_assay_of_the_silver_deposit_in_its_district(self):
        silver_grade_by_tile = {deposit.tile: deposit.ore_grade_kg_per_tonne
                                for deposit in deposits.load_deposits("silver")}
        for deposit in deposits.load_deposits("lead"):
            if deposit.tile not in silver_grade_by_tile:
                self.assertEqual(deposit.byproducts, (), deposit.name)
                continue
            self.assertEqual(len(deposit.byproducts), 1, deposit.name)
            self.assertEqual(deposit.byproducts[0].ore_grade_kg_per_tonne,
                             silver_grade_by_tile[deposit.tile], deposit.name)

    def test_lead_ore_is_dressed_before_it_is_smelted(self):
        entry = _default_production_entries()["lead_kg"]
        pool = deposits.load_deposits("lead")
        total = sum(deposit.quantity_tonnes_per_year for deposit in pool)
        rock_per_tonne_of_lead = sum(
            deposit.quantity_tonnes_per_year / total * KILOGRAMS_PER_TONNE
            / deposit.ore_grade_kg_per_tonne for deposit in pool) / LEAD_SMELTING_RECOVERY
        cupellation_air_cubic_metres = (
            OXYGEN_PER_LEAD * LEAD_PER_TONNE_KG / OXYGEN_MASS_FRACTION_OF_AIR / AIR_KG_PER_CUBIC_METRE
            * BLAST_EXCESS_OVER_STOICHIOMETRY)
        floor = (rock_per_tonne_of_lead * HAND_DRESSING_HOURS_PER_TONNE_OF_ROCK_FLOOR
                 + cupellation_air_cubic_metres / BELLOWS_CUBIC_METRES_PER_HOUR)
        self.assertGreaterEqual(entry["labour_hours"]["labourer"], floor)

    def test_cupellation_hearth_is_attended_for_the_whole_batch(self):
        entry = _default_production_entries()["lead_kg"]
        cupel_hours = LEAD_PER_TONNE_KG / BULLION_PER_CUPEL_SHIFT_KG * HOURS_PER_SHIFT
        # Two reduction passes (see the litharge test) plus the cupel.
        self.assertGreaterEqual(entry["labour_hours"]["furnaceman"], 100.0 + cupel_hours)

    def test_copper_ore_is_crushed_and_washed_before_it_is_smelted(self):
        entry = _default_production_entries()["copper_kg"]
        tonnes_of_ore = entry["inputs"]["copper_ore_kg"] / KILOGRAMS_PER_TONNE
        self.assertGreaterEqual(
            entry["labour_hours"]["labourer"],
            tonnes_of_ore * HAND_DRESSING_HOURS_PER_TONNE_OF_ROCK_FLOOR)


if __name__ == "__main__":
    unittest.main()
