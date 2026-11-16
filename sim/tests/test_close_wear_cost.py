"""A producer whose only tool has no price is costed, at the year's close and in its asks and restakes, as the Python costs it
(`unit_cost.variable_cost_per_run`): the tool covered by the cheapest step of its fallback chain, a finite cost. A non-tool
input with no price keeps the cost infinite. Each test calls one function on hand-written inputs."""
QUICK_TOPIC = True

import math
import unittest

import numpy as np

from sim.economy import close_kernel, grid_wear, unit_cost, year_arrays_costs
from sim.economy.plan_wear import covered_input_bill
from sim.economy.types import Recipe, ToolFallback
from sim.economy.year_arrays_recipes import build_recipe_matrices
from sim.economy.year_arrays_tools import tool_tables

WOOD_STEP = ToolFallback("wood", 1.0, 1.5, ("hand",))
HAND_STEP = ToolFallback("", 0.0, 2.5, ("hand",))
FARM = Recipe("farm", {"grain": 10.0}, {"seed": 1.0, "iron": 0.25}, {"hand": 100.0},
              tool_wear={"iron": 0.25}, tool_fallbacks={"iron": (WOOD_STEP, HAND_STEP)})
WAGES = {"hand": 2.0}
GOODS = ["grain", "iron", "seed", "wood"]
RATE = 0.05
ROW = np.zeros(1, dtype=np.int64)


def tables(prices):
    """(matrices, tools, price grid, area_of, wage grid) of FARM on one tile and one area, `prices` by good name (absent: NaN)."""
    matrices = build_recipe_matrices({"farm": FARM}, {}, GOODS)
    grid = np.array([[prices.get(good, np.nan)] for good in matrices.goods.ids])
    area_of = np.zeros((len(GOODS), 1), dtype=np.int64)
    wage = np.array([[WAGES[trade]] for trade in matrices.trades.ids])
    return matrices, tool_tables({"farm": FARM}, matrices), grid, area_of, wage


def inputs_bill(prices, held_by_good=None):
    matrices, tools, grid, area_of, wage = tables(prices)
    held = np.full(matrices.slot_goods.shape[1], np.nan)
    for good, found in (held_by_good or {}).items():
        held[list(matrices.slot_goods[0]).index(matrices.goods.row[good])] = found
    return grid_wear.covered_inputs_at(
        0, 0, held, matrices.slot_goods, matrices.inputs, tools, matrices.labour_hours, np.ones((1, len(matrices.trades.ids))), wage, grid,
        area_of, np.empty(tools.bid_goods.shape[1]))


class CoveredInputsAtTests(unittest.TestCase):
    def test_an_unpriced_tool_is_covered_by_its_fallback_as_the_python_covers_it(self):
        prices = {"seed": 1.5, "wood": 3.0}
        self.assertTrue(math.isfinite(inputs_bill(prices)))
        self.assertAlmostEqual(inputs_bill(prices), unit_cost.input_cost_per_run(FARM, prices, WAGES))

    def test_a_priced_tool_is_billed_at_its_price(self):
        prices = {"seed": 1.5, "iron": 8.0, "wood": 3.0}
        self.assertAlmostEqual(inputs_bill(prices), unit_cost.input_cost_per_run(FARM, prices, WAGES))

    def test_an_input_that_is_no_tool_and_has_no_price_stays_infinite(self):
        self.assertTrue(math.isinf(inputs_bill({"wood": 3.0})))

    def test_a_held_expectation_replaces_the_price_of_an_input_that_has_one(self):
        self.assertAlmostEqual(inputs_bill({"seed": 1.5, "wood": 3.0}, {"seed": 2.5}),
                               unit_cost.input_cost_per_run(FARM, {"seed": 2.5, "wood": 3.0}, WAGES))


class UnitCostsTests(unittest.TestCase):
    def costs(self, prices):
        matrices, tools, grid, area_of, wage = tables(prices)
        held = np.full((1, matrices.slot_goods.shape[1]), np.nan)
        at_price, planned = grid_wear.input_bills(ROW, ROW, held, matrices.slot_goods, matrices.inputs, tools, matrices.labour_hours, wage,
                                                  grid, area_of)
        return year_arrays_costs.unit_costs(
            ROW, ROW, np.ones(1), np.zeros(1), held, matrices.slot_goods, at_price, planned, matrices.outputs, matrices.plant_goods,
            matrices.labour_hours, matrices.plant_labour_hours, matrices.plant_life_years, grid, grid, wage, area_of, RATE, 0.3,
            matrices.outputs), list(matrices.slot_goods[0]).index(matrices.goods.row["grain"])

    def test_the_ask_cost_of_a_run_with_an_unpriced_tool_is_the_python_unit_cost(self):
        prices = {"grain": 10.0, "seed": 1.5, "wood": 3.0}
        (cost, share, _expected, _pays), slot = self.costs(prices)
        self.assertTrue(math.isfinite(cost[0, slot]))
        self.assertAlmostEqual(cost[0, slot], unit_cost.full_cost_per_unit(FARM, "grain", prices, prices, WAGES, RATE))
        self.assertAlmostEqual(share[0, slot], unit_cost.input_cost_per_run(FARM, prices, WAGES)
                               / unit_cost.variable_cost_per_run(FARM, prices, WAGES))

    def test_the_plant_share_test_counts_the_unpriced_tool_at_its_fallback(self):
        (_cost, _share, _expected, pays), _slot = self.costs({"grain": 10.0, "seed": 1.5, "wood": 3.0})
        self.assertGreater(pays[0], 0.0)

    def test_a_missing_seed_price_makes_the_cost_infinite(self):
        (cost, _share, _expected, pays), slot = self.costs({"grain": 10.0, "wood": 3.0})
        self.assertTrue(math.isinf(cost[0, slot]))
        self.assertEqual(pays[0], 0.0)


class CloseKernelWearTests(unittest.TestCase):
    def test_the_fallback_goods_the_recipe_does_not_use_are_priced_after_its_slots(self):
        matrices, tools, grid, area_of, _wage = tables({"seed": 1.5, "wood": 3.0})
        width = matrices.slot_goods.shape[1]
        prices = np.full(tools.bid_goods.shape[1], -1.0)
        close_kernel.fallback_prices(0, 0, width, tools, grid, area_of, prices)
        self.assertEqual(prices[width], 3.0)
        self.assertTrue((prices[:width] == -1.0).all())

    def test_the_variable_cost_the_close_reads_of_an_unpriced_tool_is_the_python_variable_cost(self):
        prices = {"seed": 1.5, "wood": 3.0}
        matrices, tools, grid, area_of, wage = tables(prices)
        width = matrices.slot_goods.shape[1]
        places = np.full(tools.bid_goods.shape[1], np.nan)
        for slot, column in enumerate(matrices.slot_goods[0]):
            places[slot] = grid[column, 0]
        close_kernel.fallback_prices(0, 0, width, tools, grid, area_of, places)
        inputs = covered_input_bill(0, 0, 0, matrices.slot_goods, matrices.inputs, tools, matrices.labour_hours,
                                    np.ones((1, len(matrices.trades.ids))), wage, places)
        variable = inputs + 100.0 * WAGES["hand"]
        self.assertTrue(math.isfinite(variable))
        self.assertAlmostEqual(variable, unit_cost.variable_cost_per_run(FARM, prices, WAGES))

    def test_the_return_on_capital_is_the_python_return_given_the_input_bill(self):
        prices = {"grain": 10.0, "seed": 1.5, "wood": 3.0}
        matrices = tables(prices)[0]
        count = matrices.slot_goods.shape[1]
        names = [matrices.goods.ids[column] for column in matrices.slot_goods[0]]
        output = np.array([10.0 if name == "grain" else 0.0 for name in names])
        price = np.array([prices.get(name, 0.0) for name in names])
        got = close_kernel.return_on_capital(output, price, count, unit_cost.input_cost_per_run(FARM, prices, WAGES), np.array([100.0]), 1,
                                             np.zeros(count), np.zeros(1), price, np.array([2.0]))
        self.assertAlmostEqual(got, unit_cost.return_on_capital(FARM, prices, prices, WAGES))


if __name__ == "__main__":
    unittest.main()
