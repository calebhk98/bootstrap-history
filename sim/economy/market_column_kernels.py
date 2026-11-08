"""Sums over the market memory's columns that must add in the order the markets entered the store, as the dict loops did."""
import numpy

from sim.jit import njit


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
