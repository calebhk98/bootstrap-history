"""What a market's buyers take at a price, over `crossing_columns.DemandColumns`: the arithmetic of `goods_market_demand.DemandSchedule`
(`total_at` and `uncapped_at`) bit for bit, including the order of its sums.

Where the Python adds with `sum` (Neumaier's compensated loop), the kernel adds the same numbers in the same order with
`year_close_sums.python_sum`; where it adds with `math.fsum`, with `exact_sum` (the order does not matter). Anything the kernels do
not reproduce, namely a non-finite quantity or a power the Python would raise on, sets `flags[0]` (`FALLBACK`); the caller then
runs the search on `Bid` objects, which raises or answers as before.
"""
import numpy

from sim.jit import njit

from .year_close_sums import python_sum
from .year_ledger_note_kernels import exact_sum

KERNEL = {"error_model": "numpy"}
FALLBACK = 1                    # flags[0] once a figure left the range these kernels reproduce


@njit(inline="always", **KERNEL)
def factor_at(price, reference, exponent, flags):
    """The power of the price ratio one schedule group uses. A power the Python raises on (a zero base to a negative power) flags
    the fallback; an overflow is infinity, as the Python's fallback also makes it."""
    base = price / reference
    if base == 0.0 and exponent < 0.0:
        flags[0] = FALLBACK
    return base ** exponent


@njit(inline="always", **KERNEL)
def wanted_by(floor, flexible, budget, factor, price):
    """One funded bid's quantity: its schedule capped by what its budget buys."""
    cap = budget / price
    want = floor + flexible * factor
    return cap if cap < want else want


@njit(inline="always", **KERNEL)
def free_total(demand, flags):
    """Total wanted at a price of zero or below: every funded bid's floor plus flexible units (a budget cap cannot bind on a free
    good), added exactly."""
    count = len(demand.row_floor)
    wanted = demand.row_floor + demand.row_flexible
    for row in range(count):
        if not numpy.isfinite(wanted[row]):
            flags[0] = FALLBACK
    return exact_sum(wanted, count)


@njit(inline="always", **KERNEL)
def capped_total(price, demand, flags):
    """Total wanted at a positive price when some bids have ceilings: the funded bids whose ceiling is not below the price, added
    exactly (so row order is free)."""
    wanted = numpy.empty(len(demand.row_floor))
    used = 0
    for group in range(len(demand.group_reference)):
        factor = factor_at(price, demand.group_reference[group], demand.group_exponent[group], flags)
        for row in range(demand.group_start[group], demand.group_start[group + 1]):
            if not price > demand.row_maximum[row]:
                value = wanted_by(demand.row_floor[row], demand.row_flexible[row], demand.row_budget[row], factor, price)
                if not numpy.isfinite(value):
                    flags[0] = FALLBACK
                wanted[used] = value
                used += 1
    return exact_sum(wanted, used)


@njit(inline="always", **KERNEL)
def plain_total(price, demand, flags):
    """Total wanted at a positive price when no bid has a ceiling: each group's quantities added with `sum`, in clearing order, and
    the groups' sums added one after another in first-appearance order."""
    total = 0.0
    quantities = numpy.empty(len(demand.row_floor))
    for group in range(len(demand.group_reference)):
        factor = factor_at(price, demand.group_reference[group], demand.group_exponent[group], flags)
        first, last = demand.group_start[group], demand.group_start[group + 1]
        for row in range(first, last):
            quantities[row] = wanted_by(demand.row_floor[row], demand.row_flexible[row], demand.row_budget[row], factor, price)
        total += finite_sum(quantities[first:last], last - first, flags)
    return total


@njit(inline="always", **KERNEL)
def finite_sum(values, count, flags):
    """`sum(list(values[:count]))`, flagging the fallback for a figure that is not finite (in or out)."""
    total = python_sum(values, count)
    if not numpy.isfinite(total):
        flags[0] = FALLBACK
    for position in range(count):
        if not numpy.isfinite(values[position]):
            flags[0] = FALLBACK
    return total


@njit(inline="always", **KERNEL)
def total_at(price, demand, flags):
    """Total quantity the buyers want at a price (`DemandSchedule.total_at`)."""
    if price <= 0.0:
        return free_total(demand, flags)
    if demand.capped:
        return capped_total(price, demand, flags)
    return plain_total(price, demand, flags)


@njit(inline="always", **KERNEL)
def uncapped_at(price, demand, flags):
    """Demand ignoring budgets, one step per distinct schedule (`DemandSchedule.uncapped_at`): never below `total_at`."""
    groups = len(demand.group_reference)
    terms = numpy.empty(groups)
    for group in range(groups):
        factor = factor_at(price, demand.group_reference[group], demand.group_exponent[group], flags)
        terms[group] = demand.group_floor[group] + demand.group_flexible[group] * factor
    return finite_sum(terms, groups, flags)
