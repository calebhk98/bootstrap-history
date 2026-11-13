"""A plan's input bids in the order `producers._input_bids` makes them: what the planned runs lack of each input and of the tools that
would be drawn if a tool is short, each bid for at most the budget share of its cost and no more than `producers.input_ceiling`.

Scratch arrays are the caller's, made once for all rows (a kernel allocates nothing per row)."""
import numpy as np

from sim.jit import njit

from .plan_tools import value_in_use
from .year_arrays_costs import KERNEL
from .year_close_sums import python_sum


@njit(**KERNEL)
def needs_of_row(row, recipe, runs, stock, market, slot_goods, inputs, tools, wanted_at, placed, order_place):
    """The places that carry a bid and how much each lacks, in the order they join the needs: the inputs by good, then each fallback step's
    good in step order, a good drawn by several steps (or an input) adding to the place it first took. Returns how many places; `wanted_at`
    holds the shortfall at a place and `order_place[n]` the place the nth need sits at (`placed` is scratch)."""
    placed[:] = -1
    count = 0
    for slot in range(slot_goods.shape[1]):
        good = slot_goods[recipe, slot]
        if good < 0:
            break
        if inputs[recipe, good] > 0.0 and not np.isnan(market[slot]):         # a tool with no price is covered by its fallback
            short = runs * inputs[recipe, good] - stock[row, slot]
            if short > 0.0:
                placed[slot], order_place[count], wanted_at[slot] = count, slot, short
                count += 1
    for step in range(tools.step_first.shape[1]):
        if tools.step_first[recipe, step] < 0:
            break
        place = tools.step_bid[recipe, step]
        if place < 0:
            continue
        short = runs * tools.step_units[recipe, step] - stock[row, place]
        if short > 0.0 and market[place] > 0.0:
            if placed[place] < 0:
                placed[place], order_place[count], wanted_at[place] = count, place, short
                count += 1
            else:
                wanted_at[place] = wanted_at[place] + short
    return count


@njit(**KERNEL)
def place_bids(row, recipe, tile, runs, spendable, margin, live_variable, stock, market, slot_goods, inputs, tools,
               labour_hours, hours_scale, wage, good_out, quantity_out, price_out, budget_out, worth_out, wanted_at, placed, order_place, terms):
    """Write the bids of one row at `[row, n]` in need order: the good (column, -1 where there is no nth bid), its quantity, price, budget and
    ceiling. `spendable` is the cash left after wages, `margin` and `live_variable` the run's margin and variable cost at the prices seen now."""
    count = needs_of_row(row, recipe, runs, stock, market, slot_goods, inputs, tools, wanted_at, placed, order_place)
    for need in range(count):
        place = order_place[need]
        terms[need] = wanted_at[place] * market[place]
    total_cost = python_sum(terms, count)
    for need in range(count):
        place = order_place[need]
        bid_price = market[place]
        share = wanted_at[place] * bid_price / total_cost if total_cost > 0.0 else 0.0
        worth = bid_price * (1.0 + max(0.0, margin) / live_variable) if live_variable > 0.0 else bid_price
        in_use = value_in_use(tools, labour_hours, hours_scale, wage, market, recipe, row, tile, place, terms)
        good_out[row, need] = tools.bid_goods[recipe, place]
        quantity_out[row, need], price_out[row, need] = wanted_at[place], bid_price
        budget_out[row, need] = max(0.0, spendable) * share
        worth_out[row, need] = worth if np.isnan(in_use) else min(worth, in_use)
