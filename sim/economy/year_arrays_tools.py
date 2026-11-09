"""The recipes' tool fallbacks and listed hours as tables, for the plan kernel (`plan_kernel.plan_rows`).

A recipe's tool wear is part of its inputs; what the wear adds to a plan is the fallback steps (`Recipe.tool_fallbacks`: when the
wear good is short, draw the next tool, then work by hand) held against the run as extra input bids, and the cheapest substitute
that caps what an input is bid (`tool_fallback.value_in_use`). `ToolTables` lays the steps out per recipe in the order the dict
lists them (a group per wear good, its steps in order), so the kernel walks a few entries:

    bid_goods     recipe by bid place: the good column of each place a bid can sit in. The first places are the recipe's good slots
                  (a bid sits there when the good is an input), then the fallback goods that are not inputs, in order of first mention
    step_first    recipe by step: the wear good (column) whose fallbacks the step belongs to; steps of one wear good are adjacent
    step_bid      recipe by step: the bid place of the step's good, -1 for the step that works by hand (no good)
    step_units    recipe by step: units of the good a covered run draws
    step_factor   recipe by step: the factor the covered hours of the step's trades are multiplied by
    step_trade    recipe by step and trade place: the trade column, -1 padded
    wear_good, wear_units    recipe by wear place: the wear good (column) and units a run wears, -1 / 0.0 padded
    listed_hours  recipe by trade: whether the recipe lists the trade among its hours (a listed trade bids even for zero hours)
    input_order   recipe by n: the good slot of the recipe's nth input in the order its `inputs` dict lists them, -1 padded
    hours_order   recipe by n: the trade slot of the recipe's nth hours entry in the order its `labour_hours` dict lists them, -1 padded
                  (a bill that `unit_cost` adds in dict order is added the same way by a row summed as Python sums)"""
from collections import namedtuple
from typing import Mapping

import numpy as np

from .year_arrays_recipes import NO_SLOT, RecipeMatrices

ToolTables = namedtuple("ToolTables", "bid_goods step_first step_bid step_units step_factor step_trade wear_good wear_units listed_hours "
                                      "input_order hours_order")


def fallback_goods_of(recipe) -> list:
    """The goods the recipe's fallback steps draw, in order of first mention (steps in dict order), without the empty good."""
    seen = []
    for steps in recipe.tool_fallbacks.values():
        for step in steps:
            if step.good and step.good not in seen:
                seen.append(step.good)
    return seen


def tool_tables(recipes: Mapping[str, object], matrices: RecipeMatrices) -> ToolTables:
    """The tool tables of `recipes` over the numbering of `matrices` (whose goods and trades include the fallback steps' own)."""
    count, slots = len(matrices.recipes.ids), matrices.good_slots
    goods, trades = matrices.goods.row, matrices.trades.row
    extras = [[good for good in fallback_goods_of(recipes[recipe_id]) if not matrices.inputs[row, goods[good]] > 0.0]
              for row, recipe_id in enumerate(matrices.recipes.ids)]
    steps = max([sum(len(group) for group in recipes[recipe_id].tool_fallbacks.values()) for recipe_id in matrices.recipes.ids], default=0)
    step_trades = max([len(step.trades) for recipe_id in matrices.recipes.ids for group in recipes[recipe_id].tool_fallbacks.values()
                       for step in group], default=0)
    wears = max([len(recipes[recipe_id].tool_wear) for recipe_id in matrices.recipes.ids], default=0)
    bid_goods = np.full((count, slots + max([len(each) for each in extras], default=0)), NO_SLOT, dtype=np.int64)
    bid_goods[:, :slots] = matrices.slot_goods
    step_first, step_bid = np.full((count, steps), NO_SLOT, dtype=np.int64), np.full((count, steps), NO_SLOT, dtype=np.int64)
    step_units, step_factor = np.zeros((count, steps)), np.zeros((count, steps))
    step_trade = np.full((count, steps, step_trades), NO_SLOT, dtype=np.int64)
    wear_good, wear_units = np.full((count, wears), NO_SLOT, dtype=np.int64), np.zeros((count, wears))
    listed_hours = np.zeros((count, len(matrices.trades.ids)), dtype=bool)
    input_order = np.full((count, max([len(recipes[recipe_id].inputs) for recipe_id in matrices.recipes.ids], default=0)), NO_SLOT, dtype=np.int64)
    hours_order = np.full((count, max([len(recipes[recipe_id].labour_hours) for recipe_id in matrices.recipes.ids], default=0)), NO_SLOT, dtype=np.int64)
    for row, recipe_id in enumerate(matrices.recipes.ids):
        recipe = recipes[recipe_id]
        for place, good in enumerate(extras[row]):
            bid_goods[row, slots + place] = goods[good]
        place_of = {goods[good]: place for place, good in enumerate(extras[row])}
        slot_of = {int(column): slot for slot, column in enumerate(matrices.slot_goods[row]) if column != NO_SLOT}
        step = 0
        for first, group in recipe.tool_fallbacks.items():
            for each in group:
                step_first[row, step], step_units[row, step], step_factor[row, step] = goods[first], each.units_per_run, each.hours_factor
                if each.good:
                    column = goods[each.good]
                    step_bid[row, step] = slot_of[column] if matrices.inputs[row, column] > 0.0 else slots + place_of[column]
                step_trade[row, step, :len(each.trades)] = [trades[trade] for trade in each.trades]
                step += 1
        for place, (good, units) in enumerate(recipe.tool_wear.items()):
            wear_good[row, place], wear_units[row, place] = goods[good], units
        trade_slot_of = {int(column): slot for slot, column in enumerate(matrices.slot_trades[row]) if column != NO_SLOT}
        for place, trade in enumerate(recipe.labour_hours):
            listed_hours[row, trades[trade]] = True
            hours_order[row, place] = trade_slot_of[trades[trade]]
        for place, good in enumerate(recipe.inputs):
            input_order[row, place] = slot_of[goods[good]]
    return ToolTables(bid_goods, step_first, step_bid, step_units, step_factor, step_trade, wear_good, wear_units, listed_hours, input_order, hours_order)
