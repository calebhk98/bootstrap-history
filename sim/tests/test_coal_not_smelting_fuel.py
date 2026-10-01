"""Complaints/279 (coal may stand in for charcoal where it cannot: smelting iron
before coke).

Raw coal cannot smelt metal ore before it is coked (its sulphur ruins the metal).
This test verifies that no ore-smelting recipe accepts raw coal as a fuel.
"""
import os
import unittest

from sim.engine.catalog import load_production_catalog

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


class CoalNotSmeltingFuelTests(unittest.TestCase):

    def test_no_ore_smelting_recipe_accepts_raw_coal_as_fuel(self):
        """Raw coal cannot smelt metal ore (its sulphur ruins the metal).

        Ore-smelting recipes (those with ore in inputs and metal in outputs)
        should not use raw coal as fuel. Coke is acceptable if gated on a
        coking technique. Generic heat recipes (lime, salt, brewing, smithing,
        glass) may keep coal.
        """
        production = load_production_catalog(ROOT)

        # Identify ore-smelting recipes: inputs contain 'ore', outputs contain metals
        metals_keywords = ['iron', 'copper', 'lead', 'tin', 'zinc', 'nickel', 'cobalt', 'silver']

        problematic_recipes = []

        for recipe_name, entry in production.items():
            if entry is None:
                continue

            inputs = entry.get("inputs", {})
            outputs = entry.get("outputs", {})

            # Check if this is an ore-smelting recipe
            has_ore_input = any('ore' in key for key in inputs.keys())
            produces_metal = any(any(metal in output_key for metal in metals_keywords)
                                for output_key in outputs.keys())

            # If it's an ore-smelting recipe, check that it doesn't use raw coal
            if has_ore_input and produces_metal:
                if 'coal_kg' in inputs:
                    problematic_recipes.append({
                        'recipe': recipe_name,
                        'coal_amount': inputs['coal_kg'],
                        'inputs': list(inputs.keys())
                    })

        self.assertEqual(len(problematic_recipes), 0,
                        f"Ore-smelting recipes that use raw coal (should use charcoal or coke instead): "
                        f"{problematic_recipes}")


if __name__ == "__main__":
    unittest.main()
