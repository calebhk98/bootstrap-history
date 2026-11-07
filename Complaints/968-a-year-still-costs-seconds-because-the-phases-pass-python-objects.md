# A Rome year still costs seconds because the phases hand each other Python objects

**Status:** open - the numba port (branch `speed-year-step-and-openings`, plan `docs/architecture/NUMBA_PORT_PLAN.md`) took a warm Rome year from about 20 s to about 3.5 s and stopped there; this complaint is the handoff for the redesign the one-second goal needs

This file is written so that someone who was not part of the port can pick it up with nothing else. Read it whole, then
the plan, then Complaint 497 (the speed history before the port).

## The goal and the owner's requirements

- A game is about five hundred years. A Rome year must take **under one second** of wall time; **three seconds is the
  absolute most**. Rome is the largest civilisation (about 104 tiles, about 6,800 producers, 312 household cohorts, a few
  thousand goods and labour markets); England, Norse and Mexica are several times smaller.
- **Reproducible, not bit-exact.** A ported phase may move floats in their last digits against the old Python; the rules
  must not change. The same save stepped on the same machine must give the same game, straight or saved and loaded in
  between.
- **No loss of accuracy** to buy speed: no fewer agents, no looser solves, no shortened opening.
- The game is played mostly by AI agents, often in **fresh environments on any platform** (Linux, Windows, Mac), who also
  edit the code. That is why the compiler is **numba** (`pip install numba`, carries its own LLVM, no build step, no binary
  to ship or merge). A pilot measured JAX, numba, Rust and Cython on one kernel (all compiled ones tens of times faster
  than CPython; JAX a few times; a GPU does not pay at this size: tens of thousands of small dependent steps). Do not
  switch technology without a measurement that overturns that.

## Where it stands (measure it again first)

Make a Rome save to measure on (a new game opens in a minute or two once the shipped openings match the source):

    printf '{"cmd":"state"}\n{"cmd":"quit"}\n' | python3 sim/simulator.py agent --civ rome_100ad --seed 1 --session rome_start.json
    python3 sim/simulator.py compile-kernels                      # once per environment: compiles every kernel ahead of play
    python3 sim/simulator.py year-time --session rome_start.json --years 4 --reload-check

`year-time` copies the save, steps it, prints each year's wall seconds and a digest of the game after them, and with
`--reload-check` saves and loads after the first year and checks the digest is the same. Measured at the end of the port
(three runs, a four-core machine lightly loaded): first year of a process about 6.2 to 6.7 s, later years about 3.5 to
4.5 s, typically about 3.7. Other figures at the end of the port, each with its command:

- a process's first year costs about 2 s more than its second on a warm compile cache (loading about 150 cached kernels,
  building route graphs); `year-time` first against second year
- one `agent --session` command (`echo '{"cmd":"state"}' | python3 sim/simulator.py agent --session COPY`) about 2.3 s:
  imports about 0.7, parsing the save about 0.3, the reply about 0.5, writing the save again about 0.5
- `compile-kernels` on an empty cache about one and a half to two minutes; without it a fresh environment pays that in
  its first year
- a cold opening (a new game with an empty `ROME_CACHE_DIR`): England about 4 s, Rome about 50 s for the opening solve
  (it was about ten minutes a solve before); `simulator.py openings` builds the shipped openings, one civilisation per core

## Why it stopped at a few seconds

Profile a warm year with `python3 tools/measure/warm_year_profile.py rome_start.json out.prof`. At the end of the port it
showed about 15 million calls a year (138 million before the port), about 8 s of profiled own time, and:

- about 4.9 million `dict.get` calls, 1.4 million `list.append`, about 430,000 `str.startswith` and 170,000 `str.split`
- the largest Python files by own time: `sim/book.py`, the labour package, `market_memory.py`, `settlement_batch.py`,
  `year_goods.py`, `goods_year_batch.py`
- every phase's arithmetic is a kernel and takes little of the year

The cost is at the phases' edges. Each phase receives Python objects from the one before (`Plan`, `Bid`, `Offer`,
`LabourBid`, `Fill`, `Pairing`, `ClearingResult`, `Settlement`, `GoodsMove`, `Transfer`, the ledger's dicts), packs them
into arrays, runs its kernel, and builds Python objects again for the next phase. It reads the book and the market memory
one value at a time with string keys (`good|area`, `trade|area`). Moving one store to arrays at a time does not help: the
book was moved (merged, game unchanged) and the market memory was moved (branch `port-memory-arrays`, not merged), and
neither made the year faster, because the readers still read one value at a time; for the memory, a single read through
numpy is slower than a dict read.

## What would reach one second (proposal, not settled)

Make integer-indexed arrays the interface between phases, so that from producers' plans to the close no per-bid,
per-market or per-agent Python object is built:

1. **Ids.** Number agents, goods, trades, tiles, areas and markets once for the game (growable: producers enter and leave,
   goods and trades are admitted during a game), and keep the numbering in the economy. Every hot path takes ids, never
   string keys. The year arrays (`sim/economy/year_arrays*.py`) already number producers, recipes, goods and areas per year
   and carry them across years; extend that numbering rather than start again.
2. **An order book of arrays.** Producers' plans, cohorts' orders, merchants' orders and the engine's orders write bids
   and offers into columns (buyer id, market id, floor, flexible, reference price, elasticity, budget, priority, ceiling;
   seller id, market id, quantity, reservation) instead of `Bid` and `Offer` objects. `plan_year.plans_of`,
   `households_orders_pack`, `merchants_book` and `year_goods_offers` already compute those numbers in kernels and then
   build objects: stop building the objects.
3. **Clearing results as arrays end to end.** `goods_year_results.final_allocations` already returns flows, per-bid and
   per-offer results as arrays; settlement (`settlement_arrays`, `settlement_batch`), the ledger (`year_ledger`), the market
   memory's notes and the mint should read those arrays. Labour likewise: `clearing_tail` writes one `LabourClearing` per
   market; settlement of labour and the ledger should read the arrays.
4. **The book and the memory read in blocks.** The book has `rows_of`, `balances_of`, `stocks_of`, `stocks_at`; the memory
   branch has `gather`, `positions`, `get_pair`. Every pack that reads them value by value (`close_pack`,
   `goods_respend_pack`, `year_arrays_worths`, `seller_offers`, `trade_wages`, `prices_at` and others found in the profile)
   moves to block reads; merge `port-memory-arrays` only when its readers move with it, and measure.
5. **The saved record** may keep its present format (the encode builds the plain dicts once at a save) or change: there is
   no save migration (CLAUDE.md 4.6). Within a build, save and load must round-trip (`--reload-check`).

Order of work suggested by the profile: the order book and the goods results first (they touch the most objects), then
labour's results, then the book and memory readers, then the close. Measure after each; stop a line of work that does not
show in `year-time`.

## What is already compiled, by phase (all through `sim/jit.py`)

- `sim/jit.py`: the one `njit` (nopython, no fastmath, no parallel, `cache=True`), lazy numba import, `REGISTRY` of every
  kernel; `ROME_NO_JIT=1` runs the same code as plain Python. `simulator.py compile-kernels` (`sim/ui/cli_compile_kernels.py`,
  `sim/ui/kernel_signatures.py`) compiles them all.
- Goods: `goods_market_kernels.py`, `price_setting_kernel.py`, `goods_year_kernel.py`, `goods_year_batch.py`,
  `goods_year_results.py`, `year_arrays_costs.py`, `year_goods_offers.py`; respend: `goods_respend_kernel.py` and its
  basket, market, pack and unpack modules; settlement: `settlement_kernel.py`, `settlement_batch*.py`, `settlement_arrays.py`.
- Labour (`sim/labour/market/`): `hiring_kernel.py`, `clearing_kernel.py`, `clearing_arrays.py`, `clearing_tail_kernel.py`,
  `clearing_tail.py`, `switching_kernel.py`, `sold_hours_kernel.py`, `carriage.py`.
- Producers: `plan_kernel.py`, `plan_year.py`; close: `close_kernel*.py`, `close_pack.py`, `close_run.py`,
  `year_close_producers.py`, `year_arrays_closed.py`; worths: `year_arrays_worths.py`; entry: `entry_kernels.py`,
  `entry_tables.py`; practice kernels in `practice.py`.
- Merchants: `merchants_kernel.py`, `merchants_search.py`, `merchants_book*.py`, `merchants_plan.py`, `merchants_news.py`.
- Households: `households_orders_kernel.py`, `households_orders_pack.py`.
- Opening: `opening_demand.py`, `opening_demand_kernel.py`, `opening_runs_pack.py`, `opening_runs_kernel.py`,
  `opening_hours_needed.py`.
- Geography: `routes_tree_kernel.py` (route trees).
- Year arrays: `year_arrays.py`, `year_arrays_recipes.py`, `year_arrays_producers.py`, `year_arrays_cohorts.py`,
  `year_arrays_memory.py`; built at the start of `Economy._run_year`, carried across years, synced after entry and exit.
- Kept-between-steps figures: `quiet_year.py` (country figures and shown prices, dropped by a step, a new setup or a
  memory write), `kept_wages.py`, `priced_reads.py`, `price_index.py`.

The plan's unticked items list the Python left in each phase, with the profiled cost each agent measured.

## Traps found during the port (each cost hours; check for them)

- **Python's `sum()` of floats is compensated summation since 3.12**, not left to right; and **set iteration order of
  floats** decided a summation order and a dict's key order in one rule. A kernel need not copy either (the owner allows
  last-digit moves), but a test that compares with the old path must allow for it.
- **numba does not check array bounds.** An empty market wrote one past an array's end, silently, until the plain-Python
  path raised. Run the quick tier with `NUMBA_BOUNDSCHECK=1` and a fresh `NUMBA_CACHE_DIR`, and every kernel must handle
  empty inputs.
- **numpy scalars in records.** A numpy boolean in the spin-up result stopped every new game from opening; `numpy.float64`
  passes JSON by luck, `numpy.int64` and `numpy.bool_` do not. Convert at the record boundary (`spin_up_run.plain`).
- **Every check that loads a save misses a new game's spin-up.** Also run a new game on an empty cache:
  `ROME_CACHE_DIR=<empty> agent --civ england_1300` with `state` and one `step`, exit status 0.
- **A packed snapshot can go stale inside a phase.** The opening's kernel reused the households' stock from before the
  durable stock was seeded; Rome's opening moved (8170 producers against 8189). It was found only by comparing a cold Rome
  opening with the old code's (`python3 tools/measure/opening_figures.py dump` from a checkout of each build, then
  `compare`). Compare Rome, not only England: Rome's discrete household plans react to rules England never reaches.
- **Caches keyed on a write stamp** (`market_memory.note_written` / `written_stamp`) must be bumped by every writer, including
  ones outside a step (`api.add_workers` was missing). A new cache needs a list of everything that can change its input.
- **Save and load must round-trip.** `year-time --reload-check` found two pre-existing order dependences (a sum over
  producers in live order; an int written as a float after a load). Iterate in sorted order or use `math.fsum`.
- **Shipped openings go stale on every economy edit** (their key hashes the source). A stale opening makes a new game run
  its own opening; the test harness shortens the spin-up, so it never reads shipped openings (Complaint 967).
- **Wall time on a shared machine swings by more than a small cut.** Compare profiles, and `perf_counter` wrappers around a
  phase, not only `year-time`; take before and after on the same load.

## How a change is checked (the port's protocol)

- quick tier `python3 -m sim.tests` green, also with `ROME_NO_JIT=1` and with `NUMBA_BOUNDSCHECK=1` plus a fresh
  `NUMBA_CACHE_DIR`
- each rule moved to a kernel keeps a copy of its old path in its test, run beside the kernel on random built inputs within
  a stated tolerance (the `test_year_speed_*` topics are the pattern); a case where the old path itself jumps under a
  one-ulp nudge (a discrete rule) may be skipped, saying so, and most cases must be compared
- `year-time --reload-check` reproducible, digest the same on two runs
- `python3 tools/measure/save_compare.py BEFORE.json AFTER.json` of two-year saves (`year-time --keep`): last-digit moves
  are expected; a rule change shows as more; explain what moved
- a new game on an empty cache opens and steps (above); for the opening, a cold Rome opening compared with the old code's
- `python3 sim/simulator.py compile-kernels` covers every new kernel (`sim/ui/kernel_signatures.py` for kernels the fixture
  does not reach); the slow `compile_kernels_smoke` checks it
- before a PR: `openings --prune` rebuilt, `--slow` run

If the work is shared among agents: keep their files and scratch inside the repository directory (an access outside the
working directory stops an agent on a permission prompt), give each disjoint files, and hand long runs (cold Rome
openings, the slow suite, the openings build) to whoever orchestrates.

## Related

Complaint 497 (the speed history and rounds before the port), 966 (the sample Egypt civilisation does not open), 967 (the
test runner opens every civilisation before a slow topic).
