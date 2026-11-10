"""A per-row helper that takes a wide table (many columns of mixed types) against one that takes the row's values, both for a
helper LLVM inlines and for one it does not (`inline="never"` stands in for a helper too large to inline).

    python3 -c "from tools.measure.compiled_tables import wide_tables; wide_tables.main()"
"""
import collections
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from sim.jit import njit  # noqa: E402

COLUMN_NAMES = tuple("column_%d" % index for index in range(28))
WideTable = collections.namedtuple("WideTable", COLUMN_NAMES)
ROWS = 21000
REPETITIONS = 50


def wide_table(rows):
    """Floats, integers and flags in turn, as the market memory's goods table mixes them."""
    columns = []
    for index in range(len(COLUMN_NAMES)):
        if index % 3 == 0:
            columns.append(np.random.default_rng(index).random(rows))
        elif index % 3 == 1:
            columns.append(np.arange(rows, dtype=np.int64))
        else:
            columns.append(np.zeros(rows, dtype=np.bool_))
    return WideTable(*columns)


def _value(price, count, flag):
    value = price
    for _step in range(3):
        value = value * 0.5 + count * 1e-9 + (1.0 if flag else 0.0)
    return value


value_of_row_inlined = njit(lambda table, row: _value(table.column_0[row], table.column_1[row], table.column_2[row]))
value_of_numbers_inlined = njit(lambda price, count, flag: _value(price, count, flag))
value_of_row_called = njit(inline="never")(lambda table, row: _value(table.column_0[row], table.column_1[row], table.column_2[row]))
value_of_numbers_called = njit(inline="never")(lambda price, count, flag: _value(price, count, flag))
_value = njit(_value)


@njit
def total_by_row_inlined(table, rows):
    total = 0.0
    for row in range(rows):
        total += value_of_row_inlined(table, row)
    return total


@njit
def total_by_numbers_inlined(table, rows):
    prices, counts, flags = table.column_0, table.column_1, table.column_2
    total = 0.0
    for row in range(rows):
        total += value_of_numbers_inlined(prices[row], counts[row], flags[row])
    return total


@njit
def total_by_row_called(table, rows):
    total = 0.0
    for row in range(rows):
        total += value_of_row_called(table, row)
    return total


@njit
def total_by_numbers_called(table, rows):
    prices, counts, flags = table.column_0, table.column_1, table.column_2
    total = 0.0
    for row in range(rows):
        total += value_of_numbers_called(prices[row], counts[row], flags[row])
    return total


def main():
    table = wide_table(ROWS)
    for name, function in (("table to an inlined helper", total_by_row_inlined),
                           ("numbers to an inlined helper", total_by_numbers_inlined),
                           ("table to a called helper", total_by_row_called),
                           ("numbers to a called helper", total_by_numbers_called)):
        function(table, ROWS)                       # compile outside the timing
        began = time.perf_counter()
        for _repetition in range(REPETITIONS):
            function(table, ROWS)
        print("%-30s %.3f ms per pass over %d rows" % (name, (time.perf_counter() - began) / REPETITIONS * 1000, ROWS))
