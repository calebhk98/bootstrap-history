"""Complaint 511: an ore recipe raises what a located deposit holds, at the deposit's grade, so the smelting recipe
that consumes the ore asks for at least as much ore as holds the metal it makes. A recipe that asks for less
(a few tonnes of concentrate per tonne of tin) draws almost nothing from the deposit's stock and is priced as if
the metal were free of the ore's scarcity."""

QUICK_TOPIC = True

import unittest

from sim.engine.validate_production import load_production
from sim.geography import api as geography_api

KILOGRAMS_PER_TONNE = 1000.0


def richest_grade_kg_per_tonne(resource_id):
    return max(row["ore_grade_kg_per_tonne"] for row in geography_api.deposit_records(resource_id)
               if row.get("ore_grade_kg_per_tonne"))


class OreRecipeMassBalanceTests(unittest.TestCase):
    def test_a_smelting_recipe_asks_for_ore_holding_at_least_the_metal_it_makes(self):
        production = load_production()[0]
        short = []
        for resource_id, by_ore in geography_api.ore_goods().items():
            grade = richest_grade_kg_per_tonne(resource_id)
            for ore, smelting_recipes in by_ore.items():
                for recipe_id in smelting_recipes:
                    entry = production.get(recipe_id)
                    if entry is None or entry["outputs"].get(recipe_id, 0.0) <= 0.0:
                        continue
                    metal_in_ore_kg = entry["inputs"].get(ore, 0.0) * grade / KILOGRAMS_PER_TONNE
                    if metal_in_ore_kg < entry["outputs"][recipe_id]:
                        short.append((recipe_id, ore, metal_in_ore_kg, entry["outputs"][recipe_id]))
        self.assertEqual(short, [])

    def test_tin_draws_its_gravel_from_the_deposits_at_their_grade(self):
        entry = load_production()[0]["tin_kg"]
        grade = richest_grade_kg_per_tonne("tin")
        self.assertGreaterEqual(entry["inputs"]["cassiterite_kg"] * grade / KILOGRAMS_PER_TONNE,
                                entry["outputs"]["tin_kg"])
