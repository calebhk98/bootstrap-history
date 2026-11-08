"""Ragged data: each group (an agent, a market) owns several rows of a table.

The convention: rows stay in the order they were appended, and a grouping is two arrays, `starts` (length groups + 1) and
`order` (row numbers). Group g's rows are `order[starts[g]:starts[g + 1]]`, in append order within the group. A kernel visits
a group with `for slot in range(starts[g], starts[g + 1]): row = order[slot]`. A table built once per year in group order
may skip `order` (a slot is then the row)."""
import numpy

from sim.jit import njit


@njit
def group_starts(group_of_row, row_count, group_count):
    """starts[g] is the first slot of group g; starts[group_count] is the number of rows."""
    starts = numpy.zeros(group_count + 1, dtype=numpy.int64)
    for row in range(row_count):
        starts[group_of_row[row] + 1] += 1
    for group in range(group_count):
        starts[group + 1] += starts[group]
    return starts


@njit
def stable_order(group_of_row, row_count, starts):
    """Row numbers grouped by group (a stable counting sort: rows of one group keep their append order)."""
    next_slot = starts[:-1].copy()
    order = numpy.empty(row_count, dtype=numpy.int64)
    for row in range(row_count):
        group = group_of_row[row]
        order[next_slot[group]] = row
        next_slot[group] += 1
    return order
