"""Question 5: summing each group's rows by counting-sorted order, sorted rows, linked lists and a scan.

    python3 -c "from tools.measure.compiled_tables import ragged; ragged.main()"
"""
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from sim.jit import njit  # noqa: E402


@njit
def group_starts(group_of_row, group_count):
    """starts[g]..starts[g+1] are group g's slots in a counting-sorted order."""
    starts = np.zeros(group_count + 1, np.int64)
    for row in range(group_of_row.shape[0]):
        starts[group_of_row[row] + 1] += 1
    for group in range(group_count):
        starts[group + 1] += starts[group]
    return starts


@njit
def stable_order(group_of_row, starts):
    """Row numbers grouped by group, rows of one group in their original order."""
    fill = starts[:-1].copy()
    order = np.empty(group_of_row.shape[0], np.int64)
    for row in range(group_of_row.shape[0]):
        group = group_of_row[row]
        order[fill[group]] = row
        fill[group] += 1
    return order


@njit
def total_by_order(order, starts, value):
    """CSR over a permutation: the table stays in append order."""
    out = np.zeros(starts.shape[0] - 1)
    for group in range(starts.shape[0] - 1):
        total = 0.0
        for slot in range(starts[group], starts[group + 1]):
            total += value[order[slot]]
        out[group] = total
    return out


@njit
def total_by_sorted_rows(starts, sorted_value):
    """Rows physically sorted: a slot is a row."""
    out = np.zeros(starts.shape[0] - 1)
    for group in range(starts.shape[0] - 1):
        total = 0.0
        for row in range(starts[group], starts[group + 1]):
            total += sorted_value[row]
        out[group] = total
    return out


@njit
def link_rows(group_of_row, group_count):
    """Linked lists: head[group] is the newest row, next_row[row] the next older one (-1 ends). No sort needed."""
    head = np.full(group_count, -1, np.int64)
    next_row = np.empty(group_of_row.shape[0], np.int64)
    for row in range(group_of_row.shape[0]):
        next_row[row] = head[group_of_row[row]]
        head[group_of_row[row]] = row
    return head, next_row


@njit
def total_by_links(head, next_row, value):
    out = np.zeros(head.shape[0])
    for group in range(head.shape[0]):
        total = 0.0
        row = head[group]
        while row >= 0:
            total += value[row]
            row = next_row[row]
        out[group] = total
    return out


@njit
def total_by_scan(group_of_row, group_count, value):
    out = np.zeros(group_count)
    for group in range(group_count):
        for row in range(group_of_row.shape[0]):
            if group_of_row[row] == group:
                out[group] += value[row]
    return out


def best(function, repeats=30):
    function()
    times = []
    for _ in range(repeats):
        a = time.perf_counter()
        function()
        times.append(time.perf_counter() - a)
    return 1000 * min(times)




def main():
    rng = np.random.default_rng(3)
    groups, rows = 7000, 40000          # roughly producers x holdings
    group_of_row = rng.integers(0, groups, rows).astype(np.int64)
    value = rng.uniform(0, 1, rows)
    starts = group_starts(group_of_row, groups)
    order = stable_order(group_of_row, starts)
    sorted_value = value[order]
    head, next_row = link_rows(group_of_row, groups)
    a = total_by_order(order, starts, value)
    b = total_by_sorted_rows(starts, sorted_value)
    c = total_by_links(head, next_row, value)
    print("max difference order vs sorted rows: %g, vs linked (different summation order): %g" % (abs(a - b).max(), abs(a - c).max()))
    print("build: starts+order (counting sort)   %7.3f ms" % best(lambda: stable_order(group_of_row, group_starts(group_of_row, groups))))
    print("build: linked lists                   %7.3f ms" % best(lambda: link_rows(group_of_row, groups)))
    print("pass:  CSR over a permutation         %7.3f ms" % best(lambda: total_by_order(order, starts, value)))
    print("pass:  physically sorted rows         %7.3f ms" % best(lambda: total_by_sorted_rows(starts, sorted_value)))
    print("pass:  linked lists                   %7.3f ms" % best(lambda: total_by_links(head, next_row, value)))
    print("pass:  scan all rows per group (1/50 of the groups)  %7.3f ms" % best(lambda: total_by_scan(group_of_row, groups // 50, value), 3))
    print("physically sorting 3 columns by gather: %7.3f ms" % best(lambda: (value[order], value[order], value[order])))

