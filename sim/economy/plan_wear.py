"""A plan's bill for the inputs of a run with its tools covered the cheapest way: `unit_cost.input_cost_per_run` with wages
(`tool_fallback.wear_cost_per_run`) over `year_arrays_tools.ToolTables`, added as the Python adds it.

`unit_price` holds the price of each bid place (the recipe's good slots, then the fallback goods that are not inputs; NaN: no price),
`wage` the wage of each trade on the producer's tile."""
import numpy as np

from sim.jit import njit

from .plan_tools import run_hours
from .year_arrays_costs import KERNEL


@njit(**KERNEL)
def place_of(tools, recipe, good):
    """The bid place that holds the good column `good`, -1 where the recipe has none."""
    for place in range(tools.bid_goods.shape[1]):
        if tools.bid_goods[recipe, place] == good:
            return place
    return -1


@njit(**KERNEL)
def step_bill(tools, labour_hours, hours_scale, wage, unit_price, recipe, row, tile, step):
    """`tool_fallback._step_cost` of fallback step `step`: its tool at its price plus the extra hours of its trades, the hours added in the
    step's trade order; NaN where a wage or the tool's price is missing."""
    extra = 0.0
    for place in range(tools.step_trade.shape[2]):
        trade = tools.step_trade[recipe, step, place]
        if trade < 0:
            break
        if np.isnan(wage[trade, tile]):
            return np.nan
        if tools.step_factor[recipe, step] > 1.0:
            extra += (tools.step_factor[recipe, step] - 1.0) * run_hours(labour_hours, hours_scale, recipe, row, trade) * wage[trade, tile]
    bid = tools.step_bid[recipe, step]
    if bid < 0:
        return 0.0 + extra
    if np.isnan(unit_price[bid]):
        return np.nan
    return tools.step_units[recipe, step] * unit_price[bid] + extra


@njit(**KERNEL)
def wear_bill(tools, labour_hours, hours_scale, wage, unit_price, recipe, row, tile):
    """`tool_fallback.wear_cost_per_run`: each wear good (in good order) at its price, else the first step of its chain that can be priced,
    else infinite."""
    total = 0.0
    for wear in range(tools.wear_good.shape[1]):
        good = tools.wear_good[recipe, wear]
        if good < 0:
            break
        if tools.wear_units[recipe, wear] <= 0.0:
            continue
        place = place_of(tools, recipe, good)
        if place >= 0 and not np.isnan(unit_price[place]):
            total += tools.wear_units[recipe, wear] * unit_price[place]
            continue
        covered = np.inf
        for step in range(tools.step_first.shape[1]):
            if tools.step_first[recipe, step] == good:
                cost = step_bill(tools, labour_hours, hours_scale, wage, unit_price, recipe, row, tile, step)
                if not np.isnan(cost):
                    covered = cost
                    break
        total += covered
    return total


@njit(**KERNEL)
def hard_bill(recipe, slot_goods, inputs, tools, unit_price):
    """`unit_cost._bill` of `Recipe.hard_inputs`: the inputs less the tools' wear at `unit_price`, in the recipe's dict order; infinite
    where one has no price."""
    total = 0.0
    for place in range(tools.input_order.shape[1]):
        slot = tools.input_order[recipe, place]
        if slot < 0:
            break
        good = slot_goods[recipe, slot]
        amount = inputs[recipe, good]
        for wear in range(tools.wear_good.shape[1]):
            if tools.wear_good[recipe, wear] == good:
                rest = amount - tools.wear_units[recipe, wear]
                amount = rest if rest > 1e-12 * max(1.0, amount) else 0.0
        if amount > 0.0:
            if np.isnan(unit_price[slot]):
                return np.inf
            total += amount * unit_price[slot]
    return total


@njit(**KERNEL)
def covered_input_bill(recipe, row, tile, slot_goods, inputs, tools, labour_hours, hours_scale, wage, unit_price):
    """`unit_cost.input_cost_per_run(recipe, prices, wages)`: the hard inputs, then the wear covered the cheapest way."""
    return hard_bill(recipe, slot_goods, inputs, tools, unit_price) + wear_bill(
        tools, labour_hours, hours_scale, wage, unit_price, recipe, row, tile)
