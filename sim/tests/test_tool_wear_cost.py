"""A run's cost for a tool-wear good it cannot buy is the cheapest way to cover the wear (the tool, the next tool its
basket names, or by hand), not infinity; a good that is no tool keeps the rule that a missing price stops the run.
Each test calls one function on hand-written inputs."""
QUICK_TOPIC = True

import math
import unittest

import numpy as np

from sim.economy import entry_kernels, opening_runs, tool_fallback, unit_cost
from sim.economy.types import Recipe, ToolFallback
from sim.economy.year_arrays_recipes import build_recipe_matrices
from sim.economy.year_arrays_tools import tool_tables

WOOD_STEP = ToolFallback("wood", 1.0, 1.5, ("hand",))
HAND_STEP = ToolFallback("", 0.0, 2.5, ("hand",))
FARM = Recipe("farm", {"grain": 10.0}, {"seed": 1.0, "iron": 0.25}, {"hand": 100.0},
              tool_wear={"iron": 0.25}, tool_fallbacks={"iron": (WOOD_STEP, HAND_STEP)})
WAGES = {"hand": 2.0}
WOOD_COST = 1.0 * 3.0 + 0.5 * 100.0 * 2.0
HAND_COST = 1.5 * 100.0 * 2.0


class WearCostTests(unittest.TestCase):
    def test_a_priced_tool_is_billed_at_its_price(self):
        self.assertAlmostEqual(tool_fallback.wear_cost_per_run(FARM, {"iron": 8.0, "wood": 3.0}, WAGES), 0.25 * 8.0)

    def test_an_unpriced_tool_is_covered_by_the_first_priced_step_of_its_chain(self):
        self.assertAlmostEqual(tool_fallback.wear_cost_per_run(FARM, {"wood": 3.0}, WAGES), WOOD_COST)

    def test_with_nothing_priced_the_wear_is_covered_by_hand(self):
        self.assertAlmostEqual(tool_fallback.wear_cost_per_run(FARM, {}, WAGES), HAND_COST)

    def test_a_missing_wage_leaves_the_wear_unpriceable(self):
        self.assertTrue(math.isinf(tool_fallback.wear_cost_per_run(FARM, {}, {})))

    def test_a_run_with_no_tool_wear_has_none_to_cover(self):
        self.assertEqual(tool_fallback.wear_cost_per_run(Recipe("plain", {"a": 1.0}, {"b": 1.0}, {"hand": 1.0}), {}, WAGES), 0.0)


class VariableCostTests(unittest.TestCase):
    def test_a_recipe_whose_only_tool_is_unpriced_costs_its_other_inputs_labour_and_the_fallback(self):
        got = unit_cost.variable_cost_per_run(FARM, {"seed": 1.5, "wood": 3.0}, WAGES)
        self.assertAlmostEqual(got, 1.5 + 200.0 + WOOD_COST)

    def test_a_missing_price_of_a_good_that_is_no_tool_still_stops_the_run(self):
        self.assertTrue(math.isinf(unit_cost.variable_cost_per_run(FARM, {"wood": 3.0}, WAGES)))

    def test_the_opening_ranking_keeps_a_run_whose_tool_has_no_price(self):
        costed = opening_runs.unit_costs({"farm": FARM}, {"seed": 1.5}, WAGES, 0.05)
        self.assertAlmostEqual(costed["grain"][0][0], (1.5 + 200.0 + HAND_COST) / 10.0)


def kernel_tables(recipe, prices, wages):
    """The tables the entry kernels read, for one recipe on one tile."""
    goods = sorted({*recipe.inputs, *recipe.outputs, *prices, *(step.good for steps in recipe.tool_fallbacks.values()
                                                                for step in steps if step.good)})
    matrices = build_recipe_matrices({recipe.recipe_id: recipe}, {}, goods)
    price = np.full((2, 1, len(matrices.goods.ids)), np.nan)
    for good, value in prices.items():
        price[:, 0, matrices.goods.row[good]] = value
    wage = np.full((1, len(matrices.trades.ids)), np.nan)
    for trade, value in wages.items():
        wage[0, matrices.trades.row[trade]] = value
    tools = tool_tables({recipe.recipe_id: recipe}, matrices)
    return matrices, (np.stack([matrices.inputs, matrices.outputs, matrices.plant_goods, matrices.outputs]),
                      np.stack([matrices.labour_hours, matrices.plant_labour_hours]), matrices.slot_goods, matrices.slot_trades,
                      price, wage, np.zeros((1, 2)), np.zeros((1, 2)), np.full((1, len(matrices.trades.ids)), 1.0),
                      np.array([0.5, 1.0, 1.0]), tuple(tools[:8]))


class KernelAgreesTests(unittest.TestCase):
    def test_the_entry_kernel_costs_an_unpriced_tool_as_the_python_does(self):
        for prices in ({"seed": 1.5, "wood": 3.0}, {"seed": 1.5}, {"seed": 1.5, "iron": 8.0, "wood": 3.0}):
            matrices, tables = kernel_tables(FARM, prices, WAGES)
            got = entry_kernels.full_cost_one(0, 0, matrices.goods.row["grain"], math.nan, 0.05, tables)
            want = unit_cost.full_cost_per_unit(FARM, "grain", {}, prices, WAGES, 0.05)
            self.assertTrue(math.isfinite(got), prices)
            self.assertAlmostEqual(got, want, places=9)

    def test_the_entry_kernel_still_stops_a_run_whose_ordinary_input_has_no_price(self):
        matrices, tables = kernel_tables(FARM, {"wood": 3.0}, WAGES)
        self.assertTrue(math.isinf(entry_kernels.full_cost_one(0, 0, matrices.goods.row["grain"], math.nan, 0.05, tables)))


if __name__ == "__main__":
    unittest.main()
