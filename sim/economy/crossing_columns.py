"""A market's buyers prepared for the price search, from `bid_columns.BidColumns` instead of `Bid` objects: the kernel version of
`goods_market_demand.DemandSchedule`.

The bids are taken in clearing order (`order`: the place of each bid in the order `goods_market.Buyers` sorts them, by priority, buyer
name and tile name). A bid with a budget joins the group of its schedule (reference price and elasticity; a bid whose want does not
move with the price joins the constant group), groups in the order they first appear among ALL the bids, and the funded bids are
stored group by group in clearing order, because the plain total adds each group's quantities with `sum` in that order.

`DemandColumns` (every field is a view of the prepared market; `crossing_demand.py` and `crossing_solve.py` read them):
    row_floor        units the funded bid needs at any price, grouped by schedule, clearing order inside a group   units
    row_flexible     units it takes beyond the floor at the reference price (zero in the constant group)           units
    row_budget       money the bid may spend (above zero)                                                          currency units
    row_maximum      highest price the bid accepts                                                                 currency per unit
    group_start      where each group's rows start in the row columns, with the row count at the end              row number
    group_reference  the group's reference price (one for the constant group)                                      currency per unit
    group_exponent   the power of the price ratio (negated elasticity; zero for the constant group)                pure number
    group_floor      exact sum of the group's floors (`math.fsum`)                                                 units
    group_flexible   exact sum of the group's flexible units                                                       units
    ceilings         the distinct finite maximum prices of ALL the bids, dearest first                             currency per unit
    capped           whether any bid has a finite maximum price                                                    flag
    bid_count        bids in the market, funded or not (the search spends cheap passes only when groups are few)  count
"""
from collections import namedtuple

import numpy

from sim.jit import njit

from .year_ledger_note_kernels import exact_sum

KERNEL = {"error_model": "numpy"}

DemandColumns = namedtuple("DemandColumns", (
    "row_floor", "row_flexible", "row_budget", "row_maximum", "group_start", "group_reference", "group_exponent", "group_floor",
    "group_flexible", "ceilings", "capped", "bid_count"))


@njit(**KERNEL)
def _group_of_bids(flexible, reference, elasticity, budget, order):
    """The group of each bid in clearing order, and the groups' reference prices and exponents in first-appearance order, with the
    group count. A bid without a budget, a flexible part or a reference price is in the constant group (reference one, exponent
    zero)."""
    count = len(order)
    group_of = numpy.zeros(count, dtype=numpy.int64)
    group_reference = numpy.ones(count)
    group_exponent = numpy.zeros(count)
    groups = 0
    for place in range(count):
        bid = order[place]
        key_reference, key_exponent = 1.0, 0.0
        if budget[bid] > 0.0 and flexible[bid] > 0.0 and reference[bid] > 0.0:
            key_reference, key_exponent = reference[bid], -elasticity[bid]
        found = -1
        for group in range(groups):
            if group_reference[group] == key_reference and group_exponent[group] == key_exponent:
                found = group
                break
        if found < 0:
            found = groups
            group_reference[found], group_exponent[found] = key_reference, key_exponent
            groups += 1
        group_of[place] = found
    return group_of, group_reference[:groups].copy(), group_exponent[:groups].copy(), groups


@njit(**KERNEL)
def _usable(floor, flexible, reference, elasticity, budget, maximum):
    """False when a column holds a NaN, or a funded bid's floor or flexible units are infinite: the search then runs on the objects
    (a NaN breaks the grouping; an infinite sum is not one the kernels reproduce)."""
    for bid in range(len(floor)):
        if (numpy.isnan(floor[bid]) or numpy.isnan(flexible[bid]) or numpy.isnan(reference[bid]) or numpy.isnan(elasticity[bid])
                or numpy.isnan(budget[bid]) or numpy.isnan(maximum[bid])):
            return False
        if budget[bid] > 0.0 and (numpy.isinf(floor[bid]) or numpy.isinf(flexible[bid])):
            return False
    return True


@njit(**KERNEL)
def _ceilings(maximum):
    """The distinct finite maximum prices, dearest first."""
    finite = numpy.empty(len(maximum))
    used = 0
    for bid in range(len(maximum)):
        if maximum[bid] < numpy.inf:
            finite[used] = maximum[bid]
            used += 1
    return numpy.unique(finite[:used])[::-1].copy()


@njit(**KERNEL)
def _rows_by_group(floor, flexible, reference, budget, maximum, order, group_of, groups):
    """The funded bids grouped (clearing order inside a group): their columns and where each group starts. A bid whose want does not
    move with the price keeps its floor and loses its flexible units."""
    count = len(order)
    group_start = numpy.zeros(groups + 1, dtype=numpy.int64)
    for place in range(count):
        if budget[order[place]] > 0.0:
            group_start[group_of[place] + 1] += 1
    for group in range(groups):
        group_start[group + 1] += group_start[group]
    funded = group_start[groups]
    row_floor, row_flexible = numpy.zeros(funded), numpy.zeros(funded)
    row_budget, row_maximum = numpy.zeros(funded), numpy.zeros(funded)
    next_row = group_start[:groups].copy()
    for place in range(count):
        bid = order[place]
        if budget[bid] > 0.0:
            row = next_row[group_of[place]]
            next_row[group_of[place]] += 1
            row_floor[row], row_budget[row], row_maximum[row] = floor[bid], budget[bid], maximum[bid]
            if flexible[bid] > 0.0 and reference[bid] > 0.0:
                row_flexible[row] = flexible[bid]
    return group_start, row_floor, row_flexible, row_budget, row_maximum


@njit(**KERNEL)
def _group_totals(group_start, row_floor, row_flexible):
    """The exact sum (`math.fsum`) of each group's floors and of its flexible units."""
    groups = len(group_start) - 1
    floors, flexibles = numpy.zeros(groups), numpy.zeros(groups)
    for group in range(groups):
        first, last = group_start[group], group_start[group + 1]
        floors[group] = exact_sum(row_floor[first:last], last - first)
        flexibles[group] = exact_sum(row_flexible[first:last], last - first)
    return floors, flexibles


@njit(**KERNEL)
def prepare_demand(floor, flexible, reference, elasticity, budget, maximum, order):
    """The prepared columns of a market's bids (the module docstring): whether the bids can be prepared (False: see `_usable`; the
    other results are then empty), then the group starts, the four row columns, the groups' reference prices, exponents and exact
    totals of floors and flexible units, and the ceilings."""
    empty = numpy.zeros(0)
    if not _usable(floor, flexible, reference, elasticity, budget, maximum):
        return False, numpy.zeros(1, dtype=numpy.int64), empty, empty, empty, empty, empty, empty, empty, empty, empty
    group_of, group_reference, group_exponent, groups = _group_of_bids(flexible, reference, elasticity, budget, order)
    group_start, row_floor, row_flexible, row_budget, row_maximum = _rows_by_group(
        floor, flexible, reference, budget, maximum, order, group_of, groups)
    group_floor, group_flexible = _group_totals(group_start, row_floor, row_flexible)
    return (True, group_start, row_floor, row_flexible, row_budget, row_maximum, group_reference, group_exponent, group_floor,
            group_flexible, _ceilings(maximum))


def demand_columns(columns, order):
    """`DemandColumns` of a market's `BidColumns` taken in `order` (the clearing order); None when the columns cannot be prepared."""
    (usable, group_start, row_floor, row_flexible, row_budget, row_maximum, group_reference, group_exponent, group_floor,
     group_flexible, ceilings) = prepare_demand(columns.floor, columns.flexible, columns.reference, columns.elasticity, columns.budget,
                                                columns.maximum, order)
    if not usable:
        return None
    return DemandColumns(row_floor, row_flexible, row_budget, row_maximum, group_start, group_reference, group_exponent, group_floor,
                         group_flexible, ceilings, len(ceilings) > 0, len(order))
