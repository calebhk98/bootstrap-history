"""Speed: the year-end price reads that are kept between calls (the recipes making a good, the memory's price kinds and
recently traded goods, a recipe's sorted pairs) equal a fresh computation and are dropped when what they read changes.
Each test calls one function on inputs written out in the test; no game."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory import PRICE_REMEMBERED, PRICE_SMOOTHED_TRADE, MarketMemory
from sim.economy.recipes import recipes_making
from sim.economy.types import QUOTE_LOWEST_UNFILLED_ASK, Recipe


def recipe(recipe_id, outputs, inputs=None, tool_wear=None):
    return Recipe(recipe_id, outputs, inputs or {}, {}, tool_wear=tool_wear or {})


def plain_makers(recipes, good):
    return [each for each in recipes.values() if each.outputs.get(good, 0.0) > 0.0]


class RecipesMakingAGood(unittest.TestCase):
    def test_same_recipes_in_the_same_order_as_the_scan(self):
        recipes = {"c": recipe("c", {"salt": 1.0, "tin": 0.0}), "a": recipe("a", {"salt": 2.0}), "b": recipe("b", {"tin": 1.0})}
        for good in ("salt", "tin", "iron"):
            self.assertEqual([each.recipe_id for each in recipes_making(recipes, good)],
                             [each.recipe_id for each in plain_makers(recipes, good)])

    def test_a_replaced_mapping_is_read_afresh_and_a_grown_one_too(self):
        recipes = {"a": recipe("a", {"salt": 2.0})}
        self.assertEqual(len(recipes_making(recipes, "salt")), 1)
        grown = {**recipes, "b": recipe("b", {"salt": 1.0})}
        self.assertEqual(len(recipes_making(grown, "salt")), 2)
        recipes["z"] = recipe("z", {"salt": 1.0})
        self.assertEqual(len(recipes_making(recipes, "salt")), 2)


class RecipeSortedPairs(unittest.TestCase):
    def test_outputs_hard_inputs_and_tool_wear_are_sorted_pairs(self):
        made = recipe("r", {"b": 1.0, "a": 2.0}, {"y": 3.0, "x": 4.0, "tool": 1.0}, tool_wear={"tool": 1.0})
        self.assertEqual(made.outputs_sorted, (("a", 2.0), ("b", 1.0)))
        self.assertEqual(made.hard_inputs_sorted, (("x", 4.0), ("y", 3.0)))
        self.assertEqual(made.tool_wear_sorted, (("tool", 1.0),))


class PriceKindsByGood(unittest.TestCase):
    def memory(self):
        return MarketMemory(prices={"grain|a": 1.0, "grain|b": 1.0, "salt|a": 2.0}, trade_age={"grain|b": 0, "salt|a": 3})

    def test_equals_a_fresh_work_out(self):
        memory = self.memory()
        self.assertEqual(memory.price_kinds_by_good(), memory._worked_out_price_kinds())
        self.assertEqual(memory.price_kinds_by_good()["grain"], PRICE_SMOOTHED_TRADE)

    def test_dropped_when_a_trade_age_a_quote_or_a_price_is_written(self):
        memory = self.memory()
        self.assertEqual(memory.price_kinds_by_good()["salt"], PRICE_REMEMBERED)
        memory.set_quote_kind("salt|a", QUOTE_LOWEST_UNFILLED_ASK)
        self.assertEqual(memory.price_kinds_by_good()["salt"], QUOTE_LOWEST_UNFILLED_ASK)
        memory.note_trading(["salt|a"])
        self.assertEqual(memory.price_kinds_by_good()["salt"], PRICE_SMOOTHED_TRADE)
        memory.set_price("tin|a", 1.0)
        self.assertIn("tin", memory.price_kinds_by_good())

    def test_dropped_when_the_stores_are_replaced_whole(self):
        memory = self.memory()
        memory.price_kinds_by_good()
        memory.prices = {"grain|x": 1.0}
        memory.trade_age = {}
        self.assertEqual(list(memory.price_kinds_by_good()), ["grain"])

    def test_the_answer_handed_out_is_a_copy(self):
        memory = self.memory()
        memory.price_kinds_by_good().clear()
        self.assertTrue(memory.price_kinds_by_good())


class GoodsTradedWithin(unittest.TestCase):
    def test_equals_the_scan_and_follows_the_trade_ages(self):
        memory = MarketMemory(prices={"grain|a": 1.0, "salt|a": 2.0}, trade_age={"grain|a": 0, "salt|a": 3})
        self.assertEqual(memory.goods_traded_within(2), {"grain"})
        self.assertEqual(memory.goods_traded_within(3), {"grain", "salt"})
        memory.note_trading([])
        self.assertEqual(memory.goods_traded_within(0), set())
        memory.goods_traded_within(0).add("junk")
        self.assertEqual(memory.goods_traded_within(0), set())


if __name__ == "__main__":
    unittest.main()
