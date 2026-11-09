"""The tool fallbacks of a plan, as kernels over `year_arrays_tools.ToolTables`: what a short wear good costs a run to replace, and the
most an input is therefore bid (`tool_fallback.value_in_use` and `producers._input_bids`, rule for rule).

A bid place is a place in the row of bids (the recipe's good slots, then the fallback goods that are not inputs); `market` holds the
price each place is bought at (NaN: none) and `wage` the wage of each trade on the producer's tile."""
import numpy as np

from sim.jit import njit

from .exact_sum import exact_sum
from .year_arrays_costs import KERNEL


@njit(**KERNEL)
def run_hours(labour_hours, hours_scale, recipe, row, trade):
    """The hours a run asks of `trade`: the booked hours times what the producer's crew practice multiplies them by."""
    return labour_hours[recipe, trade] * hours_scale[row, trade]


@njit(**KERNEL)
def step_hours_cost(tools, labour_hours, hours_scale, wage, recipe, row, tile, step, terms):
    """`tool_fallback._extra_hours_cost`: what the extra hours of a covered run of `step` cost, NaN when a trade of the step has no wage.
    `terms` is scratch for the sum."""
    factor = tools.step_factor[recipe, step]
    for place in range(tools.step_trade.shape[2]):
        trade = tools.step_trade[recipe, step, place]
        if trade < 0:
            break
        if np.isnan(wage[trade, tile]):
            return np.nan
    if not factor > 1.0:
        return 0.0
    used = 0
    for place in range(tools.step_trade.shape[2]):
        trade = tools.step_trade[recipe, step, place]
        if trade < 0:
            break
        terms[used] = (factor - 1.0) * run_hours(labour_hours, hours_scale, recipe, row, trade) * wage[trade, tile]
        used += 1
    return exact_sum(terms, used)


@njit(**KERNEL)
def step_cost(tools, labour_hours, hours_scale, wage, market, recipe, row, tile, step, terms):
    """`tool_fallback._step_cost`: a run's extra cost when `step` covers the work (its tool at its price, plus the extra hours); NaN
    where the tool has no price or a wage is missing."""
    hours = step_hours_cost(tools, labour_hours, hours_scale, wage, recipe, row, tile, step, terms)
    if np.isnan(hours):
        return np.nan
    place = tools.step_bid[recipe, step]
    if place < 0:
        return 0.0 + hours
    if np.isnan(market[place]):
        return np.nan
    return tools.step_units[recipe, step] * market[place] + hours


@njit(**KERNEL)
def cheapest_after(tools, labour_hours, hours_scale, wage, market, recipe, row, tile, first, after, terms):
    """The lowest `step_cost` among the steps of the wear good `first` that come after step `after` (-1: all of them); NaN when none can be priced."""
    lowest = np.nan
    for step in range(after + 1, tools.step_first.shape[1]):
        if tools.step_first[recipe, step] != first:
            if after >= 0:
                break
            continue
        cost = step_cost(tools, labour_hours, hours_scale, wage, market, recipe, row, tile, step, terms)
        if not np.isnan(cost) and (np.isnan(lowest) or cost < lowest):
            lowest = cost
    return lowest


@njit(**KERNEL)
def value_in_use(tools, labour_hours, hours_scale, wage, market, recipe, row, tile, place, terms):
    """`tool_fallback.value_in_use` of the good at bid place `place`: what a unit of it saves a run against the cheapest substitute that
    comes after it (as the first of a wear, or as a later fallback), the largest over the ways it is used; NaN when it is no tool or
    nothing after it can be priced."""
    good = tools.bid_goods[recipe, place]
    best = np.nan
    for wear in range(tools.wear_good.shape[1]):
        if tools.wear_good[recipe, wear] == good:
            lowest = cheapest_after(tools, labour_hours, hours_scale, wage, market, recipe, row, tile, good, -1, terms)
            if not np.isnan(lowest):
                value = max(0.0, lowest - 0.0) / tools.wear_units[recipe, wear]
                best = value if np.isnan(best) or value > best else best
    for step in range(tools.step_bid.shape[1]):
        if tools.step_bid[recipe, step] == place and tools.step_units[recipe, step] > 0.0:
            own = step_hours_cost(tools, labour_hours, hours_scale, wage, recipe, row, tile, step, terms)
            lowest = cheapest_after(tools, labour_hours, hours_scale, wage, market, recipe, row, tile, tools.step_first[recipe, step], step, terms)
            if not np.isnan(own) and not np.isnan(lowest):
                value = max(0.0, lowest - own) / tools.step_units[recipe, step]
                best = value if np.isnan(best) or value > best else best
    return best
