"""A table spec: the columns of a table with a one-line meaning and a unit each, and the namedtuple type built from it.

A table is a namedtuple whose fields are numpy columns of one length (its capacity) plus two bookkeeping fields:
`row_count` (how many rows are in use) and `capacity` (how many fit), each a one-element array so a kernel can change
them. Rows `0 .. row_count - 1` are in use; a row's number is its id in the table's `IdTable` when it has one.

The namedtuple class must live at module level in the module that declares the spec (`Loans = LOANS.make_type(__name__)`)
so numba can cache kernels that take it: the cache pickles the type by module and name. Columns are whole 1-d arrays
(never slices of a bigger array: a slice has another memory layout and makes numba compile a second copy of the kernel)."""
import collections
from typing import Iterable, NamedTuple, Optional

import numpy

BOOKKEEPING = ("row_count", "capacity")


class Column(NamedTuple):
    """One column: its name, numpy dtype, one-line meaning, unit and, for a column holding ids, the id table's name.
    A column with a `width` (an integer, or 0 when `new_table` is told the width) holds that many values per row (people per
    ability band): a 2-d array of shape (capacity, width), read as `table.people[row, band]`; no width is a plain 1-d column."""
    name: str
    dtype: object
    meaning: str
    unit: str
    ids: Optional[str] = None
    width: Optional[int] = None


class TableSpec:
    """The columns of a table, in order, and the functions that build its tables."""

    def __init__(self, type_name: str, columns: Iterable[Column]):
        self.type_name = type_name
        self.columns = tuple(columns)
        names = [column.name for column in self.columns]
        for name in names:
            if name.startswith("_") or name in dir(tuple) or name in BOOKKEEPING:
                raise ValueError("column name %r clashes with the tuple's own names" % name)
        if len(set(names)) != len(names):
            raise ValueError("table %s repeats a column name" % type_name)
        if not self.columns:
            raise ValueError("table %s has no columns" % type_name)

    def make_type(self, module_name: str):
        """The namedtuple class for this spec, tagged with the module that holds it (pass `__name__`)."""
        fields = BOOKKEEPING + tuple(column.name for column in self.columns)
        return collections.namedtuple(self.type_name, fields, module=module_name)

    def column(self, name: str) -> Column:
        for column in self.columns:
            if column.name == name:
                return column
        raise KeyError("table %s has no column %r" % (self.type_name, name))

    def new_table(self, table_type, capacity: int, row_count: int = 0, widths=None):
        """An all-zero table with room for `capacity` rows, `row_count` of them in use. `widths` ({column: width}) sets
        the width of the columns whose width is only known when the table is made."""
        if not 0 <= row_count <= capacity:
            raise ValueError("row_count %d does not fit capacity %d" % (row_count, capacity))
        widths = widths or {}
        columns = []
        for column in self.columns:
            width = widths.get(column.name, column.width)
            columns.append(numpy.zeros(capacity if width is None else (capacity, width), dtype=column.dtype))
        return table_type(numpy.array([row_count], dtype=numpy.int64), numpy.array([capacity], dtype=numpy.int64), *columns)

    def table_of(self, table_type, **values):
        """A full table from one sequence per column, all of one length (a test or a load builds its rows this way)."""
        lengths = {len(sequence) for sequence in values.values()}
        if len(lengths) != 1 or set(values) != {column.name for column in self.columns}:
            raise ValueError("table %s needs every column, all the same length" % self.type_name)
        rows = lengths.pop()
        table = self.new_table(table_type, rows, rows)
        for column in self.columns:
            getattr(table, column.name)[:] = values[column.name]
        return table

    def describe_columns(self) -> str:
        """The spec as readable text: one line per column with its dtype, unit and meaning."""
        return "\n".join("%s: %s [%s] %s" % (column.name, numpy.dtype(column.dtype).name, column.unit, column.meaning)
                         for column in self.columns)
