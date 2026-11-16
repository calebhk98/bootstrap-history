"""The entry kernels' bill for the wear of a recipe's tools: `tool_fallback.wear_cost_per_run` over the arrays.

`wear` is the first eight arrays of `year_arrays_tools.ToolTables`: bid_goods, step_first, step_bid, step_units, step_factor,
step_trade, wear_good, wear_units (their layout is documented there). A fallback step's good is the column
`bid_goods[r, step_bid]`; a step that works by hand has `step_bid` -1."""
import numpy as np

from sim.jit import njit

NO_SLOT = -1


@njit
def step_cost(r, t, step, hours, price, wage, wear):
    """tool_fallback._step_cost of fallback step `step` of recipe row `r` at tile `t`'s prices and wages: its tool at the
    price per unit plus the extra hours of its trades; infinite where a price or a wage is missing."""
    bid_goods, _first, step_bid, step_units, step_factor, step_trade = wear[0], wear[1], wear[2], wear[3], wear[4], wear[5]
    extra = 0.0
    for place in range(step_trade.shape[2]):
        trade = step_trade[r, step, place]
        if trade == NO_SLOT:
            break
        pay = wage[t, trade]
        if np.isnan(pay):
            return np.inf
        if step_factor[r, step] > 1.0:
            extra += (step_factor[r, step] - 1.0) * hours[0, r, trade] * pay
    bid = step_bid[r, step]
    if bid == NO_SLOT:
        return extra
    found = price[0, t, bid_goods[r, bid]]
    if np.isnan(found):
        return np.inf
    return step_units[r, step] * found + extra


@njit
def wear_bill(r, t, hours, price, wage, wear):
    """tool_fallback.wear_cost_per_run: each wear good at its price, else the first step of its chain that can be priced,
    else infinite."""
    step_first, wear_good, wear_units = wear[1], wear[6], wear[7]
    total = 0.0
    for place in range(wear_good.shape[1]):
        good = wear_good[r, place]
        if good == NO_SLOT:
            break
        units = wear_units[r, place]
        if units <= 0.0:
            continue
        found = price[0, t, good]
        if not np.isnan(found):
            total += units * found
            continue
        covered = np.inf
        for step in range(step_first.shape[1]):
            if step_first[r, step] == good:
                cost = step_cost(r, t, step, hours, price, wage, wear)
                if np.isfinite(cost):
                    covered = cost
                    break
        total += covered
    return total
