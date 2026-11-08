# Compiled tables: the conventions every converter follows

Why: a warm year spends most of its time in the Python around the kernels, packing and unpacking per-item objects
(Complaint 968). The plan is to keep the year's state in shared tables that compiled code reads and writes, so no per-item
Python object crosses between phases. This file fixes the shape of those tables. The code is `sim/compiled_tables/`; the
measurements are `tools/measure/compiled_tables/`. Numbers below come from a small shared machine and move run to run: each
has its command, and what matters is the ratio, which the commands show again. The decisions below rest on ratios of several
times or more, not on differences inside the noise.

## The pieces, in one place

| Need | Use | File |
|---|---|---|
| A table with named, documented columns | `TableSpec` + `Column`; the table is a `collections.namedtuple` of numpy columns; a column with a `width` holds that many values per row (`table.people[row, band]`) | `spec.py` |
| Names to dense numbers | `IdTable` (sorted batches, saved as a name list) | `ids.py` |
| Rows added during a phase | `reserve_rows` in Python, `claim_row` in the kernel | `growth.py` |
| Several rows per agent or market | `group_starts` + `stable_order` | `grouping.py` |
| A sum | `ordered_total` | `sums.py` |
| An error from a kernel | an integer code from a `Causes` tuple, named at the boundary | `causes.py` |
| A row for a log line or an error | `describe_row` | `describe.py` |
| A worked, documented example | `example_loans.py` (columns with meaning and unit, small kernels) | |

## 1. Named tables inside kernels: a namedtuple of arrays

Decision: **`collections.namedtuple`, declared at module level from a `TableSpec`**, passed to an `njit(cache=True)` kernel and read
as `table.column[row]`.

- Disk cache: a kernel taking a namedtuple loads from `__pycache__` in a second process. Measured with
  `python3 -c "from tools.measure.compiled_tables import table_kinds; table_kinds.main()"` run twice after deleting
  `tools/measure/compiled_tables/__pycache__`: the namedtuple kernel's first call was about 70 ms cold (compile) and about 3 ms
  warm (load). The example kernels in `sim/compiled_tables/example_loans.py` went from about 0.5 s plus 0.2 s cold to a few
  milliseconds each warm, after the one-time cost of the process's first cached call (about 0.1 s, the same for plain-array
  kernels); the loading script is in `table_kinds.py`'s docstring.
- Two things stop the cache: the class defined in the script being run (`__main__`) rather than an importable module, and a
  column that is a slice (another array layout, so a second specialization). `TableSpec.make_type(__name__)` and
  whole-array columns avoid both; `test_compiled_tables_spec` checks the type pickles by module and name, which is what the cache
  needs, and `test_compiled_tables_growth` checks grown columns stay whole.
- A third stops it silently: the spec's name differs from the module attribute holding the type
  (`Requests = TableSpec("ClearingRequests", ...).make_type(__name__)`). The cache is written but never found on load, so every
  process compiles the kernel again. Name the spec as the attribute; `python3 tools/check_table_names.py` (run by
  `tools/done_check.sh`) lists any table type held under another name.
- `ROME_NO_JIT=1`: the same code runs unchanged as plain Python (the tests run both ways:
  `ROME_NO_JIT=1 python3 -m sim.tests --only compiled_tables_ids,compiled_tables_spec,compiled_tables_growth,compiled_tables_grouping,compiled_tables_sums,compiled_tables_loans --jobs 1`).
  Plain Python is about two orders of magnitude slower for a 1000-row loop, as `table_kinds` prints; that is for debugging.
- `structref` and `jitclass`: neither loads from the cache in the measurement (the constructor is compiled every process: about 0.1
  to 0.2 s each in `table_kinds`; jitclass is documented not to cache, confirmed). Both also fail the plain-Python requirement, since
  they exist only inside numba. Per-call cost at the Python boundary is within noise of the namedtuple (about one microsecond;
  unpacking a namedtuple argument costs a fraction of a microsecond more than passing the arrays as separate arguments, paid once
  per kernel entry, never inside a kernel).
- Every table also carries two one-element arrays, `row_count` and `capacity`, because a namedtuple is immutable and a kernel must
  be able to change the count. Rows `0 .. row_count - 1` are in use; code that reads a column past `row_count` is a bug.

## 2. Small functions cost nothing measurable

Decision: **write many small `njit` helpers that call each other.** Measured on a batch of small markets (bisection for a clearing
price over a few bids each) written as one large kernel and as four helpers
(`demand_at`, `supply_at`, `clearing_price`, `quantity_traded`):

- Time: `python3 -c "from tools.measure.compiled_tables import small_functions; small_functions.main()"` prints large and small
  alternating; they are equal within the noise of a shared machine.
- Instructions: with `PYTHONHASHSEED=0 NUMBA_CPU_NAME=generic valgrind --tool=cachegrind --cache-sim=no python3 -c "from
  tools.measure.compiled_tables import small_functions; small_functions.main('small', N)"` (kernels compiled beforehand, N = 0 and
  40, 'large' and 'small'), the difference N = 40 minus N = 0 was the same for both to within a few percent, the helpers slightly
  fewer.
- Inlining: the assembly of the helper-based kernel contains no call to any helper (`kernel.inspect_asm()`; the LLVM before
  optimisation does have the calls). LLVM inlines the helpers, so the split is free.
- Cost of a helper that is *not* inlined is a call, not a Python boundary. The one thing that does cost is rebuilding a table value
  in a loop (section 4).
- A helper that takes a **wide table** (many columns of mixed types) per row costs the same as one that takes the row's
  numbers, whether LLVM inlines it or not:
  `python3 -c "from tools.measure.compiled_tables import wide_tables; wide_tables.main()"` times the four cases on a
  28-column table. (A report during the market-memory conversion of a far larger cost for the table form was not
  reproduced; its slow version was not kept.) Unpacking the columns a kernel needs at its top
  (`prices, held = markets.price, markets.held`) is still the house style, because it names what the kernel reads.

## 3. Ids: `IdTable`

Decision: one `IdTable` per kind of thing (agents, goods, areas, markets), owned by the module that owns the things, **numbered in
sorted batches and saved as the list of names.**

- Dense numbers from 0; `admit(names)` numbers the names not seen before in sorted order among themselves, so the numbering does
  not depend on the iteration order of a dict or set. Admitting is the only way a number is made.
- Order must not depend on history (CLAUDE.md): the numbering is part of the saved state (`state()` is the ordered list;
  `from_state` restores it exactly, without re-sorting). A loaded game then numbers, and therefore sums, as the live one did. The
  alternative (renumber everything sorted at load) would differ from a live game that admitted goods mid-game, so it is not used.
  Per-year numberings that are rebuilt from scratch each year (the current `sim/economy/year_arrays*.py`, rows in sorted id order)
  satisfy the rule by being sorted every year; a numbering carried across years uses `IdTable`.
- A number is never reused while a game runs. A leaver stays as a dead row (a column such as `alive` or a closing year in the
  table that uses the id); `compacted(keep)` drops the dead at a year boundary and returns an old-to-new array that every table
  holding those ids applies once (`DROPPED` marks a number that is gone).
- The prototype's `Numbering` (`git show goods-order-book-prototype:sim/economy/book_numbering.py`) numbers in arrival order and
  is per year's book, which is fine for a book rebuilt each year but not for a numbering that outlives it; its `ranks()` trick
  (sort by name through a rank array) is not needed when ids are admitted sorted, but a table that mixed batches can still ask
  `sorted(names)` of the `IdTable` at the boundary when it needs name order.
- Debugging: `IdTable.describe(number)` gives `wheat#12` (and shows an out-of-range number rather than raising);
  `describe_row(spec, table, row, {"agents": agent_ids})` shows a whole row with its id columns turned into names, for logs and the
  text of an error. A `Column(..., ids="agents")` marks which columns hold ids.
- A missing name is `None` from `find` and `KeyError` from `number`; there is no sentinel number that looks real (CLAUDE.md).

## 4. Growable tables: reserve at the boundary, claim in the kernel

Decision: **Python reserves capacity once per phase for an upper bound (`reserve_rows`), the kernel appends with `claim_row`, and
`claim_row` returns `NO_ROOM` instead of writing past the end.** Measured (`python3 -c "from tools.measure.compiled_tables import
growth; growth.main()"`, a million rows of three columns):

| Pattern | Result |
|---|---|
| presized table, count inside the table (A) | same as presized plain arrays |
| reserve once with a known bound, from a small start (B) | same as A |
| Python doubles and calls the kernel per chunk (D) | a few times A, still milliseconds |
| the kernel calls `reserve` before every append (C), or only when full (C2) | more than thirty times slower |

C is slow because the table value is rebuilt inside the loop, so numba cannot keep the arrays in registers and counts references
on every pass. So: no growth inside the hot loop. If a phase cannot bound its additions, it returns a cause code (`table_full`)
when `claim_row` says `NO_ROOM`, Python reserves more, and the phase is rerun from its start (so a phase that appends must be
restartable: it reads inputs and writes only its own output tables, which are cleared by resetting `row_count`).

## 5. Ragged data: one convention, `starts` and `order`

Decision: **a grouping is `starts` (length groups + 1) and `order` (row numbers, stable within a group).** Rows stay in append order;
group g's rows are `order[starts[g]:starts[g + 1]]`. A table built once per year already in group order drops `order` and a slot is the
row. This is the CSR layout; "sorted rows with group starts" is the same thing with `order` as the identity. Measured with
`python3 -c "from tools.measure.compiled_tables import ragged; ragged.main()"` (40,000 rows in 7,000 groups):

- building the grouping: a counting sort, well under a millisecond; linked lists (head and next) build about three times faster
- a pass over every group: through `order` about a third slower than physically sorted rows, linked lists about twice the sorted
  pass (and they visit a group newest first, a different summation order)
- a scan of all rows for each group: dozens of times slower (this is what a per-market Python loop over a flat table turns into)

The counting sort is stable, so within a group rows keep their append order, which fixes the summation order (section 7). Pick sorted
rows for tables written once per year (gather the columns once: about as cheap as one pass) and `order` for tables that are appended
to during a phase.

## 6. Strings never enter a kernel

Decision: **ids and numbers only.** A kernel can compare strings (`python3 -c "from tools.measure.compiled_tables import
strings_and_sums; strings_and_sums.main()"` prints the cost): about a hundred times slower per comparison than comparing ids, and a
string array cannot be a column of a table that should load from the cache and run under plain numpy. For text:

- A kernel that refuses or fails returns a **small whole number**; `Causes(("table_full", ...))` gives each name its code, a module
  constant (`TABLE_FULL = CAUSES.code("table_full")`) the kernel can return, and `CAUSES.refusal(code, text, **facts)` builds the
  `sim.refusal.Refusal` at the boundary, with the figures in `facts` (read values, not wording, in tests).
- The boundary builds the text: it turns the row into names with `describe_row` and the ids' `IdTable.describe`. A kernel that wants
  to say which row failed returns the row too (a second output array or a `(code, row)` pair), never a formatted message.
- Raising from a kernel works for programmer errors (a bad index), not as the normal way to report a refusal.

## 7. Floats and order

- A kernel adds a column **left to right in row order**, with `ordered_total` or an explicit loop. numba's loop and `values.sum()` do
  that; numpy's `sum`, `dot` and `@` add pairwise in blocks, so under `ROME_NO_JIT=1` they give other last digits than the compiled
  run (`strings_and_sums.py` prints all four). `math.fsum` is not available in nopython. So: no `.sum()`, `np.dot`, `@` or
  `np.cumsum` for a figure that must match between a compiled and a plain run; use `ordered_total` or a loop.
- Row order is id order (section 3), and ids are admitted in sorted batches and saved, so a live game and a loaded one sum the
  same rows in the same order. Within a group the order is append order (section 5). No fastmath and no parallel loops
  (`sim/jit.py`), so nothing reassociates a sum.
- Reproducible, not bit-exact against the old Python: a port may change last digits once, then the same save on the same machine
  must give the same game, straight or saved and loaded in between (`simulator.py year-time --reload-check`).

## Readability rules for converters

1. **Every column is declared with a `Column` giving a one-line meaning and a unit** (`"currency units"`, `"kg"`, `"fraction per
   year"`, `"agent id"`). A table with an undocumented column is not merged. `example_loans.py` is the model.
2. **Every kernel has a docstring** saying what it reads, what it writes and what it returns. Comment the why of a line, never the
   history.
3. **Spelled-out names** (CLAUDE.md naming): `bid_price`, `market_number`, `loans`; the only short names are `i` and `x`/`y`.
   Columns are named for the thing, not the array (`principal`, not `principal_array`).
4. **A function short enough to read whole** (about a screen): one rule per kernel, built from small helpers. Section 2 shows this
   costs nothing. A phase kernel is a loop that calls helpers; arithmetic with a name (`interest_due`) is its own helper.
5. **Tables, not objects, between phases.** A phase takes tables and returns or fills tables; it builds no per-item Python object
   (`Bid`, `Fill`, `Settlement`) for the next phase. Python objects exist at the boundary (a player's view, a log line), built
   from a table row on demand.
6. **No strings, no dicts, no lists of objects in a kernel**; no `.sum()` for a figure that matters (section 7); no growth inside a
   loop (section 4).
7. **Each kernel gets a test that calls it on a handful of rows** it writes out (see `test_compiled_tables_loans.py`) and runs under
   numba and `ROME_NO_JIT=1`. A kernel that is only reached through a whole game is not tested.
8. **Heuristics keep their label** (CLAUDE.md 4.4) in the table's column meaning or the kernel's docstring, with the `retire`.

## Reproducing everything

    python3 -m sim.tests --only compiled_tables_ids,compiled_tables_spec,compiled_tables_growth,compiled_tables_grouping,compiled_tables_sums,compiled_tables_loans --jobs 1
    ROME_NO_JIT=1 python3 -m sim.tests --only compiled_tables_ids,compiled_tables_spec,compiled_tables_growth,compiled_tables_grouping,compiled_tables_sums,compiled_tables_loans --jobs 1
    python3 -c "from tools.measure.compiled_tables import table_kinds; table_kinds.main()"
    python3 -c "from tools.measure.compiled_tables import small_functions; small_functions.main()"
    python3 -c "from tools.measure.compiled_tables import growth; growth.main()"
    python3 -c "from tools.measure.compiled_tables import ragged; ragged.main()"
    python3 -c "from tools.measure.compiled_tables import strings_and_sums; strings_and_sums.main()"
