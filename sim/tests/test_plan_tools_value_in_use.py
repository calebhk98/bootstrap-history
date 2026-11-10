"""`plan_tools.value_in_use` (a kernel over `year_arrays_tools.ToolTables`) gives what `tool_fallback.value_in_use` gives for a recipe written out here:
the largest saving a unit of the tool makes against the cheapest substitute that comes after it, as the first of a wear and as a later
fallback, at the prices and wages written out and with a crew whose practice stretches the recipe's hours."""

QUICK_TOPIC = True

import unittest
from dataclasses import replace

import numpy as np

from sim.economy import practice, tool_fallback
from sim.economy.plan_tools import value_in_use
from sim.economy.types import Recipe, ToolFallback
from sim.economy.year_arrays_recipes import build_recipe_matrices
from sim.economy.year_arrays_tools import tool_tables

GOODS = ("anvil", "board", "flour", "hammer", "nail", "tongs", "wheat")
RECIPE = Recipe(
    "forge", {"wheat": 2.0, "hammer": 0.4, "tongs": 0.1}, {"flour": 1.5}, {"smith": 2.0, "miller": 1.0}, tool_wear={"hammer": 0.4, "tongs": 0.1},
    tool_fallbacks={"hammer": (ToolFallback("anvil", 0.3, 1.25, ("smith",)), ToolFallback("board", 0.5, 1.4, ("smith", "miller")),
                               ToolFallback("", 0.0, 2.5, ("smith", "miller"))),
                    "tongs": (ToolFallback("board", 0.2, 1.1, ("smith",)),)})
PRICES = {"anvil": 3.0, "board": 0.8, "flour": 1.0, "hammer": 6.0, "nail": 0.1, "tongs": 2.0, "wheat": 0.5}
WAGES = {"miller": 1.5, "smith": 2.5}


class ToolValueInUse(unittest.TestCase):

    def arrays(self, prices, crew_runs):
        """(tables, matrices, market by bid place, wage by trade and tile, hours scale of the row) for RECIPE at `prices` and a crew."""
        recipes = {"forge": RECIPE}
        matrices = build_recipe_matrices(recipes, {}, GOODS)
        tools = tool_tables(recipes, matrices)
        market = np.full(tools.bid_goods.shape[1], np.nan)
        for place, column in enumerate(tools.bid_goods[0]):
            if column >= 0 and matrices.goods.ids[column] in prices:
                market[place] = prices[matrices.goods.ids[column]]
        wage = np.array([[WAGES[trade]] for trade in matrices.trades.ids])
        scale = np.ones((1, len(matrices.trades.ids)))
        for trade, runs in crew_runs.items():
            scale[0, matrices.trades.row[trade]] = practice.practised_multiplier(runs)
        return tools, matrices, market, wage, scale

    def check(self, prices, crew_runs, good):
        tools, matrices, market, wage, scale = self.arrays(prices, crew_runs)
        place = int(np.flatnonzero(tools.bid_goods[0] == matrices.goods.row[good])[0])
        found = value_in_use(tools, matrices.labour_hours, scale, wage, market, 0, 0, 0, place, np.zeros(8))
        wanted = tool_fallback.value_in_use(practice.recipe_for(RECIPE, crew_runs), good, prices, WAGES)
        if wanted is None:
            self.assertTrue(np.isnan(found), (good, found))
        else:
            self.assertEqual(found, wanted, good)
        return wanted

    def test_the_first_tool_of_a_wear(self):
        self.assertGreater(self.check(PRICES, {}, "hammer"), 0.0)

    def test_the_first_tool_with_a_stretched_crew(self):
        self.assertGreater(self.check(PRICES, {"smith": 2.0, "miller": 7.0}, "hammer"), 0.0)

    def test_a_later_tool_is_worth_what_the_fallbacks_after_it_save(self):
        self.assertIsNotNone(self.check(PRICES, {"smith": 3.0}, "anvil"))

    def test_a_tool_that_is_a_fallback_of_two_wears(self):
        self.assertIsNotNone(self.check(PRICES, {}, "board"))

    def test_a_substitute_without_a_price_is_left_out(self):
        self.check({good: price for good, price in PRICES.items() if good != "anvil"}, {}, "hammer")
        self.assertIsNone(self.check({good: price for good, price in PRICES.items() if good not in ("board",)}, {}, "tongs"))

    def test_a_good_that_is_no_tool(self):
        self.assertIsNone(self.check(PRICES, {}, "wheat"))


if __name__ == "__main__":
    unittest.main()
