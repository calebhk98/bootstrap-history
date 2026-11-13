"""A run's bill for its inputs with the tools covered the cheapest way (`unit_cost.input_cost_per_run` with wages), at the prices
of a tile read from the price grids: `plan_wear.covered_input_bill` over the places of a recipe's bids (`year_arrays_tools`).

An input with no price makes the bill infinite; a tool with no price is covered by the first step of its fallback chain that can
be priced. Wages are the grid `wage[trade, tile]`; the hours of a step are the recipe's booked hours."""
import numpy as np

from sim.jit import njit

from .plan_wear import covered_input_bill
from .year_arrays_costs import KERNEL, price_in


@njit(**KERNEL)
def covered_inputs_at(recipe, tile, held, slot_goods, inputs, tools, labour_hours, unscaled, wage, price, area_of, places):
    """The bill of recipe `recipe`'s inputs on `tile`. A good with a price is bought at the producer's own expectation `held`
    (by slot; NaN: none) where it is an input and has one, else at the price (producers.expected_input_prices). `places` is
    scratch, one per bid place; `unscaled` is one row of ones, the booked hours."""
    slots = slot_goods.shape[1]
    for place in range(places.shape[0]):
        good = tools.bid_goods[recipe, place]
        found = price_in(price, area_of, good, tile) if good >= 0 else np.nan
        if place < slots and not np.isnan(found) and inputs[recipe, good] > 0.0 and not np.isnan(held[place]):
            found = held[place]
        places[place] = found
    return covered_input_bill(recipe, 0, tile, slot_goods, inputs, tools, labour_hours, unscaled, wage, places)


@njit(**KERNEL)
def input_bills(recipe_row, tile_row, held_expected, slot_goods, inputs, tools, labour_hours, wage, price, area_of):
    """By producer row: (the bill of a run's inputs at the prices of its tile, the same at the prices a plan costs them at)."""
    count = recipe_row.shape[0]
    unscaled = np.ones((1, labour_hours.shape[1]))
    none_held = np.full(slot_goods.shape[1], np.nan)
    places = np.empty(tools.bid_goods.shape[1])
    at_price, planned = np.empty(count), np.empty(count)
    for row in range(count):
        recipe, tile = recipe_row[row], tile_row[row]
        at_price[row] = covered_inputs_at(recipe, tile, none_held, slot_goods, inputs, tools, labour_hours, unscaled, wage, price, area_of, places)
        planned[row] = covered_inputs_at(recipe, tile, held_expected[row], slot_goods, inputs, tools, labour_hours, unscaled, wage, price,
                                         area_of, places)
    return at_price, planned
