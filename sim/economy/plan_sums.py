"""The sums of a plan, in the two orders the kernel adds them in (`plan_kernel.plan_rows`).

A row planned with `python_sums` false adds a bill left to right over the recipe's good (or trade) slots, in sorted order. A row planned with
`python_sums` true adds each sum as `producers.plan` does: a bill (`unit_cost._bill`) left to right in the order the recipe's dict lists its
entries, a built-in `sum` of floats as CPython 3.12 and later does (`python_sum`), `math.fsum` exactly (`exact_sum`). The kernel plans every
producer; the rows `producers.plan` planned before it did (tool fallbacks, stretched hours) keep Python's sums, and the others keep the
order they have been added in, so a saved game plays on to the same last digit.
retire: when the digests of the speed checks are recorded again, every row is summed as Python sums (`python_sums` true everywhere)."""
import numpy as np

from sim.jit import njit

from .exact_sum import exact_sum
from .plan_tools import run_hours
from .year_arrays_costs import KERNEL
from .year_close_sums import python_sum


@njit(**KERNEL)
def revenue_per_run(python_sums, recipe, slot_goods, outputs, expected, terms):
    """`unit_cost.revenue_per_run`: the outputs at their expected prices (NaN: none), those without left out."""
    total = 0.0
    used = 0
    for slot in range(slot_goods.shape[1]):
        good = slot_goods[recipe, slot]
        if good < 0:
            break
        if outputs[recipe, good] > 0.0 and not np.isnan(expected[slot]):
            term = outputs[recipe, good] * expected[slot]
            terms[used] = term
            used += 1
            total += term
    return exact_sum(terms, used) if python_sums else total


@njit(**KERNEL)
def input_bill(python_sums, recipe, slot_goods, inputs, input_order, unit_price):
    """`unit_cost.input_cost_per_run`: the inputs at `unit_price` by good slot, added in sorted order or in the recipe's dict order."""
    total = 0.0
    if python_sums:
        for place in range(input_order.shape[1]):
            slot = input_order[recipe, place]
            if slot < 0:
                break
            quantity = inputs[recipe, slot_goods[recipe, slot]]
            if quantity > 0.0:
                total += quantity * unit_price[slot]
        return total
    for slot in range(slot_goods.shape[1]):
        good = slot_goods[recipe, slot]
        if good < 0:
            break
        if inputs[recipe, good] > 0.0:
            total += inputs[recipe, good] * unit_price[slot]
    return total


@njit(**KERNEL)
def held_value_of(python_sums, row, recipe, slot_goods, inputs, input_order, capacity, stock, market, terms):
    """The value at market prices of what is held of each input, up to a full year's use at capacity, added as the plan adds it."""
    total = 0.0
    used = 0
    if python_sums:
        for place in range(input_order.shape[1]):
            slot = input_order[recipe, place]
            if slot < 0:
                break
            quantity = inputs[recipe, slot_goods[recipe, slot]]
            if quantity > 0.0:
                terms[used] = min(stock[row, slot], quantity * capacity) * market[slot]
                used += 1
        return python_sum(terms, used)
    for slot in range(slot_goods.shape[1]):
        good = slot_goods[recipe, slot]
        if good < 0:
            break
        if inputs[recipe, good] > 0.0:
            total += min(stock[row, slot], inputs[recipe, good] * capacity) * market[slot]
    return total


@njit(**KERNEL)
def hours_bill(python_sums, row, recipe, tile, slot_trades, hours_order, labour_hours, hours_scale, wage, terms):
    """(`unit_cost.labour_cost_per_run`, the run's hours, the hours priced by `joint_labour_ceilings`, whether every hired trade has a wage): the
    run's hours at the wages of the tile, added in sorted order, or in the recipe's dict order with the compensation of `sum` for the hours and
    their bill the ceilings add. `terms` is scratch of twice the trade slots."""
    cost = 0.0
    hours_total = 0.0
    priced = True
    used = 0
    half = slot_trades.shape[1]
    width = hours_order.shape[1] if python_sums else slot_trades.shape[1]
    for place in range(width):
        slot = hours_order[recipe, place] if python_sums else place
        if slot < 0:
            break
        trade = slot_trades[recipe, slot]
        if trade < 0:
            break
        hours = run_hours(labour_hours, hours_scale, recipe, row, trade)
        if hours > 0.0:
            hours_total += hours
            if np.isnan(wage[trade, tile]):
                priced = False
            else:
                cost += hours * wage[trade, tile]
                terms[used], terms[half + used] = hours, hours * wage[trade, tile]
                used += 1
    if python_sums:
        return cost, python_sum(terms, used), python_sum(terms[half:], used), priced
    return cost, hours_total, cost, priced
