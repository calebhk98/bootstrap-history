"""Shared tables for the compiled year: named columns, dense ids, growth, grouping, ordered sums, coded problems.

The rules every converter follows are in docs/architecture/COMPILED_TABLES.md. The pieces:

    spec.py        Column and TableSpec: a table is a namedtuple of numpy columns, each documented by its spec
    ids.py         IdTable: names to dense whole numbers, the same numbering live and after a load
    growth.py      reserve_rows (Python, before a kernel) and claim_row (kernel): rows appended into spare capacity
    grouping.py    group_starts and stable_order (kernels): each group's rows as a slice of an order array
    sums.py        ordered_total (kernel): the one way a kernel adds a column
    causes.py      Causes: problem codes a kernel returns and the boundary turns into named, readable refusals
    describe.py    describe_row: one row as names and values, for debugging and error messages
    example_loans.py  a small documented table and its kernels, used by the tests

Kernels take numbers, numpy arrays and namedtuples of them, never strings (`sim/jit.py` compiles them)."""
