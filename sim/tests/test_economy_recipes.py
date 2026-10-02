"""Production data as recipes, and the order goods clear in."""
import unittest

from sim.economy import recipes
from sim.economy.types import Recipe
from sim.world.demand import production_data


def entry(outputs, inputs=None, **fields):
    base = {"outputs": outputs, "inputs": inputs or {}, "labour_hours": {}}
    base.update(fields)
    return base


class MappingTests(unittest.TestCase):
    def test_joint_outputs_inputs_labour_and_energy_carriers_are_kept(self):
        data = {"lead_kg": entry({"lead_kg": 1000.0, "silver_kg": 1.5}, {"galena_kg": 1500.0},
                                 labour_hours={"smelter": 20.0}, thermal_mj=500.0, land_hectare_years=1.0)}
        recipe = recipes.recipes_from_production_data(data)["lead_kg"]
        self.assertEqual(dict(recipe.outputs), {"lead_kg": 1000.0, "silver_kg": 1.5})
        self.assertEqual(dict(recipe.inputs), {"galena_kg": 1500.0, "thermal_mj": 500.0})
        self.assertEqual(dict(recipe.labour_hours), {"smelter": 20.0})
        self.assertNotIn("hectare_land", recipe.inputs)

    def test_capital_becomes_plant_per_run_of_yearly_capacity_on_the_longest_life(self):
        capital = [{"build_materials": {"stone_kg": 400.0}, "build_labour_hours": {"mason": 40.0},
                    "service_life_years": 40, "annual_output_at_basis": 400.0},
                   {"build_materials": {"brick": 3.0}, "service_life_years": 4, "annual_output_at_basis": 400.0}]
        recipe = recipes.recipes_from_production_data({"x": entry({"x": 100.0}, capital=capital)})["x"]
        self.assertAlmostEqual(recipe.plant_goods["stone_kg"], 100.0)     # 4 runs a year of capacity
        self.assertAlmostEqual(recipe.plant_goods["brick"], 3.0 * 10 / 4.0)    # rebuilt ten times in the life
        self.assertAlmostEqual(recipe.plant_labour_hours["mason"], 10.0)
        self.assertEqual(recipe.plant_life_years, 40.0)

    def test_only_allowed_entries_load(self):
        data = {"a": entry({"a": 1.0}), "b": entry({"b": 1.0})}
        self.assertEqual(sorted(recipes.recipes_from_production_data(data, ["b", "missing"])), ["b"])

    def test_real_production_files_load(self):
        loaded = recipes.recipes_from_production_data(production_data())
        self.assertGreater(len(loaded), 250)
        self.assertTrue(all(isinstance(recipe, Recipe) and recipe.outputs for recipe in loaded.values()))
        self.assertIn("land_hectare_years", recipes.unmapped_field_counts(production_data()))


class DepthOrderTests(unittest.TestCase):
    def test_ore_comes_before_metal_in_real_data(self):
        order = recipes.input_depth_order(recipes.recipes_from_production_data(production_data()))
        self.assertLess(order.index("iron_ore_kg"), order.index("pig_iron_kg"))
        self.assertLess(order.index("pig_iron_kg"), order.index("iron_bar_kg"))

    def test_a_chain_is_ordered_inputs_first(self):
        data = {"c": entry({"c": 1.0}, {"b": 1.0}), "b": entry({"b": 1.0}, {"a": 1.0}), "a": entry({"a": 1.0})}
        self.assertEqual(recipes.input_depth_order(recipes.recipes_from_production_data(data)), ["a", "b", "c"])

    def test_a_cycle_is_ordered_by_name_and_the_same_every_time(self):
        data = {"x": entry({"x": 1.0}, {"y": 1.0, "ore": 1.0}), "y": entry({"y": 1.0}, {"x": 1.0}),
                "metal": entry({"metal": 1.0}, {"x": 1.0})}
        for keys in (["x", "y", "metal"], ["metal", "y", "x"]):
            ordered = {key: data[key] for key in keys}
            order = recipes.input_depth_order(recipes.recipes_from_production_data(ordered))
            self.assertEqual(order, ["ore", "x", "y", "metal"])

    def test_a_good_that_consumes_itself_is_not_its_own_dependency(self):
        data = {"seed": entry({"seed": 3.0}, {"seed": 1.0})}
        self.assertEqual(recipes.input_depth_order(recipes.recipes_from_production_data(data)), ["seed"])


if __name__ == "__main__":
    unittest.main()
