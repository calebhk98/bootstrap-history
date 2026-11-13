"""A producer whose tool has no live price plans its runs with the tool covered by its fallback chain, the cost a run pays
(`tool_fallback.wear_cost_per_run`), not infinity; the plan kernel's bill is the Python bill. Each test calls one function."""
QUICK_TOPIC = True

import math
import unittest

import numpy as np

from sim.economy import plan_wear, producers, unit_cost
from sim.economy.types import Recipe, ToolFallback
from sim.economy.year_arrays_recipes import build_recipe_matrices
from sim.economy.year_arrays_tools import tool_tables
from sim.tests.test_economy_producer_wide_margin_plan import View

WOOD_STEP = ToolFallback("wood", 1.0, 1.5, ("hand",))
HAND_STEP = ToolFallback("", 0.0, 2.5, ("hand",))
FARM = Recipe("farm", {"grain": 10.0}, {"seed": 1.0, "iron": 0.25}, {"hand": 100.0},
              tool_wear={"iron": 0.25}, tool_fallbacks={"iron": (WOOD_STEP, HAND_STEP)})
WAGES = {"hand": 2.0}


def farmer():
    return producers.Producer(agent_id="f1", owner="o", recipe_id="farm", tile="t", capacity_runs=100.0, last_runs=0.0,
                              expected_sales=50.0, expected_prices={"grain": 10.0, "seed": 1.5})


def farm_view():
    return View({"grain": 10.0, "seed": 1.5, "wood": 3.0}, WAGES)


class PlanOfAnUnpricedToolTests(unittest.TestCase):
    def test_such_a_producer_with_a_positive_margin_and_expected_sales_plans_runs(self):
        plan = producers.plan(farmer(), FARM, farm_view(), 1e6)
        self.assertGreater(plan.runs, 0.0)

    def test_its_wage_line_is_what_its_runs_pay_in_wages(self):
        plan = producers.plan(farmer(), FARM, farm_view(), 1e6)
        self.assertAlmostEqual(plan.wage_line, plan.runs * unit_cost.labour_cost_per_run(FARM, WAGES))

    def test_the_input_bids_do_not_bid_for_the_unpriced_tool_but_for_the_wooden_one(self):
        plan = producers.plan(farmer(), FARM, farm_view(), 1e6)
        self.assertNotIn("iron", [bid.good for bid in plan.bids])
        self.assertIn("wood", [bid.good for bid in plan.bids])


class KernelWearBillTests(unittest.TestCase):
    def bill(self, prices):
        matrices = build_recipe_matrices({"farm": FARM}, {}, ["grain", "iron", "seed", "wood"])
        tools = tool_tables({"farm": FARM}, matrices)
        unit_price = np.full(tools.bid_goods.shape[1], np.nan)
        for place, column in enumerate(tools.bid_goods[0]):
            if column >= 0 and matrices.goods.ids[column] in prices:
                unit_price[place] = prices[matrices.goods.ids[column]]
        wage = np.array([[WAGES[trade]] for trade in matrices.trades.ids])
        return plan_wear.covered_input_bill(0, 0, 0, matrices.slot_goods, matrices.inputs, tools, matrices.labour_hours,
                                            np.ones((1, len(matrices.trades.ids))), wage, unit_price)

    def test_the_kernel_bills_an_unpriced_tool_as_the_python_does(self):
        for prices in ({"seed": 1.5, "wood": 3.0}, {"seed": 1.5}, {"seed": 1.5, "iron": 8.0, "wood": 3.0}):
            self.assertEqual(self.bill(prices), unit_cost.input_cost_per_run(FARM, prices, WAGES), prices)

    def test_the_kernel_still_stops_a_run_whose_ordinary_input_has_no_price(self):
        self.assertTrue(math.isinf(self.bill({"wood": 3.0})))


if __name__ == "__main__":
    unittest.main()
