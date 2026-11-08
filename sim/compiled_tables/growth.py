"""Growing a table: spare capacity and a count, reserved once per phase.

`reserve_rows` runs in Python at a phase boundary with an upper bound on the rows the phase will add (one bid per bidder, one
loan per borrower). The kernel then calls `claim_row` for each new row and never reallocates. Reserving before every append
inside a kernel measured far slower (docs/architecture/COMPILED_TABLES.md, question 4), so kernels do not grow tables."""
import numpy

from sim.jit import njit

NO_ROOM = -1       # claim_row's answer when the table is full: the caller returns a problem code, never writes past the end


def reserve_rows(table, extra: int):
    """The same table when `extra` more rows fit, else a copy with room for them (capacity at least doubles)."""
    needed = int(table.row_count[0]) + extra
    capacity = int(table.capacity[0])
    if needed <= capacity:
        return table
    new_capacity = max(needed, 2 * capacity)
    columns = []
    for name, column in zip(table._fields, table):
        if name == "row_count":
            columns.append(column)
        elif name == "capacity":
            columns.append(numpy.array([new_capacity], dtype=numpy.int64))
        else:
            grown = numpy.zeros((new_capacity,) + column.shape[1:], dtype=column.dtype)
            grown[:capacity] = column
            columns.append(grown)
    return type(table)(*columns)


@njit
def claim_row(table):
    """The number of a new row at the end of the table, now counted as in use, or NO_ROOM when the table is full."""
    row = table.row_count[0]
    if row >= table.capacity[0]:
        return NO_ROOM
    table.row_count[0] = row + 1
    return row
