"""Sums over the market memory's columns that must add in the order the markets entered the store, as the dict loops did."""
import numpy

from sim.jit import njit

from .opening_demand_kernel import PARTIALS, _add, _total


@njit
def add_in_order_by_group(groups, values, group_count):
    """Per group number below `group_count`: the sum of its `values`, added left to right in the order given (so the same float as
    `total = total + value` over a dict's items), and the order in which the groups first appear (`first_seen`, -1 padded) with how many did."""
    totals = numpy.zeros(group_count)
    seen = numpy.zeros(group_count, dtype=numpy.bool_)
    first_seen = numpy.full(group_count, -1, dtype=numpy.int64)
    appeared = 0
    for place in range(len(groups)):
        group = groups[place]
        if not seen[group]:
            seen[group] = True
            first_seen[appeared] = group
            appeared += 1
        totals[group] += values[place]
    return totals, first_seen, appeared


@njit
def traded_price_by_group(ends, kept, price, counted_weight):
    """The national price of each group of places (`ends` the end of each group's run): the sum of price times weight over the group's
    places, over the sum of their weights, both exact (the `math.fsum` figures), where the weights sum to more than nothing; else the price of
    the group's first kept place. `counted_weight` is zero at a place that is dropped or not a trade. Returns (price per group, whether
    the group has a kept place)."""
    groups = len(ends)
    answer = numpy.zeros(groups)
    exists = numpy.zeros(groups, dtype=numpy.bool_)
    partials = numpy.zeros(PARTIALS)
    start = 0
    for group in range(groups):
        end = ends[group]
        first = -1
        for place in range(start, end):
            if kept[place]:
                first = place
                break
        if first >= 0:
            exists[group] = True
            count = 0
            for place in range(start, end):
                count = _add(partials, count, counted_weight[place])
            quantity = _total(partials, count)
            if quantity > 0.0:
                count = 0
                for place in range(start, end):
                    count = _add(partials, count, price[place] * counted_weight[place])
                answer[group] = _total(partials, count) / quantity
            else:
                answer[group] = price[first]
        start = end
    return answer, exists
