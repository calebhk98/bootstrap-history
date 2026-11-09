# A Rome year still costs seconds: the Python between the kernels is spread over the whole year

**Status:** partly - branch `year-speed-caching-and-order-book` took a warm Rome year from about 4 s to about 2.3 s of process time (results unchanged but for last digits); this file is the handoff for the rest of the way to one second

This file is written so that someone who was not part of the work can pick it up with nothing else. Read it whole, then
`docs/architecture/COMPILED_YEAR.md` (what each phase now is, phase by phase, and what is left in it) and
`docs/architecture/COMPILED_TABLES.md` (the table conventions). Complaint 497 has the history before the numba port.

## The goal and the owner's requirements

- A game is about five hundred years. A Rome year must take **under one second** of wall time; **three seconds is the
  absolute most**. Rome is the largest civilisation; England, Norse and Mexica are several times smaller.
- **Reproducible, not bit-exact.** A change may move floats in their last digits; the rules must not change. The same save
  stepped on the same machine must give the same game, straight or saved and loaded in between.
- **No loss of accuracy** to buy speed: no fewer agents, no looser solves, no coarser searches, no shortened opening.
- **Readable.** Objects and classes are the programming interface; arrays sit underneath. Comments, spelled-out names, small
  functions. The owner's words: if the code is too slow, readability is not useful, but both are wanted.
- The compiler stays **numba** (`sim/jit.py`; reasons in the numba port plan, `docs/architecture/NUMBA_PORT_PLAN.md`). Do
  not switch technology without a measurement that overturns it.

## Where it stands (measure it again first)

The measure saves are made as in the old text: `printf '{"cmd":"state"}\n{"cmd":"quit"}\n' | python3 sim/simulator.py agent
--civ rome_100ad --seed 1 --session rome_start.json` (and `england_1300` for England), then `python3 sim/simulator.py
compile-kernels` once.

Measured at the handoff (a four-core machine, otherwise quiet, three alternating runs each, every run warm):

| Figure | main | this branch | Command |
|---|---|---|---|
| warm Rome year, process time | about 3.9 to 4.1 s | about 2.2 to 2.4 s | `python3 tools/measure/warm_year_cpu.py rome_start.json` (main has no such tool: the same steps by hand, load, step a year, time a second `game.step()` with `time.process_time()`) |
| warm Rome year, wall | not measured at the handoff | about 2.1 to 2.5 s | `python3 sim/simulator.py year-time --session rome_start.json --years 2 --reload-check` (second figure) |
| warm England year, wall | not measured | about 0.6 to 1.4 s | the same with `england_start.json --years 5` |
| time inside compiled kernels, warm Rome year | not measured | about 0.7 s | `python3 tools/measure/warm_year_split_profile.py rome_start.json out.prof`, sum of the `kernel__` entries |
| profiled function calls, warm Rome year | not measured | about 3.9 million | the same profile |

The instruction counts of the final branch against main are in the pull request (`year-time --count-instructions`).

So the three-second limit is met and the one-second goal is not. The kernels alone are about 0.7 s; the Python left in
the year is about 1.5 s, spread so thinly that no single function has more than a few hundredths of a second of own time.

## What this branch did (pointers, not a list of everything)

- **The book, the market memory and the year ledger are tables** (`sim/compiled_tables/`: `TableSpec` namedtuples of numpy
  columns, `IdTable` numberings, exact sum kernels). Producers (`ProducerStore`), cohorts (`CohortStore`) and merchants
  (`MerchantTable`) are column stores; `Producer`, `Cohort` and `Merchant` are snapshots or handles made on demand. A warm
  year builds no `Producer`, no `Cohort` and no `PricedNeed` object.
- **Kernels over whole phases where the rule allows:** producers' plans (every producer, `plan_kernel.plan_rows`), the
  goods clearing per good (the per-good numpy chains are kernels: `goods_rows_kernel`, `goods_pack_kernel`,
  `goods_decide_inputs_kernel`, `goods_clearing_kernel`, ...), settlement numbering and ledger columns, merchant dispatch
  (one call a year), merchant learning, close and credit, the government's keep, assessments and revenue, revolts, entry
  plan loops, labour offers and reach, the price response.
- **Faster kernels, same answers:** the book index hash, columns held in hot loops instead of whole tables passed per row,
  the respend logs sized so it runs once.
- **Cached views** on channels (the shadow check `SHADOW_CHECK_EVERY` in `sim/engine/game_assembly.py` verifies them).
- **Tools:** `tools/measure/warm_year_split_profile.py`, `warm_year_cpu.py`, `numpy_calls_per_good.py`,
  `clear_goods_python_time.py`, `year-time --count-instructions`, `tools/check_table_names.py`.
- **Correctness fixes found on the way:** numba's cache served stale compiled callers after a callee changed in another
  file (now keyed on source, `sim/kernel_cache.py`); market numbering followed string-hash order (canonical numbering); a
  log line could not carry a fact named `cause` (`sim/refusal.py`); loan clearing recompiled in every process (a table
  class whose name differed from its module attribute).

## Why it stopped at about 2.3 s: what was measured

The plan assumed the Python was per-object glue that would disappear once the data were columns. Measured package by
package (process time, alternating base and branch), that was mostly wrong:

- Removing every `PricedNeed` (thousands a year), every `Cohort` snapshot, the merchants' per-merchant loops, the book's
  single-value reads, the labour glue and the close's dict walks each gave a change within run-to-run noise.
- Cutting the numpy calls per good in the goods loop by more than ten times gave no measurable change.
- The one clear gain of the last part of the work was the producer and memory reads as blocks (about a third of a second).
- The kernel-speed work took the kernels from about 0.8 to about 0.7 s.

What the split profile shows now: about 0.7 s in kernels, and the rest of the year as ordinary Python (loops, dict and
list work, attribute reads, small numpy calls) spread over every phase. By phase, profiled and so inflated (cProfile about
doubles Python), kernels included, largest first: the goods clearing loop (`year_goods.clear_goods`), labour clearing
(`year_labour.clear_labour`), the close (`year_close.close_agents`), household orders (`year_order_sources.cohort_orders`),
the money phases outside the economy (`year_steps.money_world`, mostly the governments' `advance`), entry
(`entry_year.open_entrants`), merchant dispatch, producers' plans, lending (`Economy._lend`), land (`land_market.settle_year`),
hour supply (`Economy._hour_supply`), merchant orders. Run the profile and read it with:

    python3 tools/measure/warm_year_split_profile.py rome_start.json out.prof
    python3 -c "import pstats; s=pstats.Stats('out.prof'); s.sort_stats('cumulative').print_stats('economy/(year_|economy)', 30)"

To reach one second the Python must fall from about 1.5 s to about 0.3 s: most of it, everywhere. No single conversion
left on the list below is worth more than a few percent.

## What is left, by phase (each with where it stops and why)

Each item names what an agent found and why it stopped there. The per-phase sections of `COMPILED_YEAR.md` hold the same
with more detail.

- **Goods clearing loop** (`year_goods.clear_goods`, `for good in order`). It must stay a loop over goods in order: between
  one good's settlement and the next good's clearing, the producers' turn (`goods_turn.produce`) reads the stocks and cash
  the earlier goods posted, and offers read the cash shortfall. Posting once at the end would change a rule. Left inside:
  - the producers' turn: `goods_turn._post` (builds posting tables from about fifteen small arrays, then the
    `apply_postings` kernel), `goods_turn.offer` (a chain of numpy calls around `offer_pairs`, `reservations_for`, `_write`);
    a kernel over the posting tables and `reservations_for` is not written
  - `settle_good`: `post_settled_by_numbers` and `note_settlement_rows` write the book and ledger per good
  - `goods_order_book.goods_with_orders`: the flush of waiting `Bid` objects into rows; the order makers should write rows
  - respend: `goods_respend_pack.pack` is Python over objects (`bid_rows`, `offer_rows`, `read_stocks`, `need_of_good`)
  - kernels: `goods_year_kernel.decide_markets` is the largest kernel of the year (the price search; nearly every
    candidate price is distinct, so there is nothing to share; `raise_search` recomputes demand per offer at each bisection
    step, an estimated small saving); `respend_rounds`; `final_allocations`
- **The structural option for this loop:** one kernel per good that runs turn, clear and settle with the book's columns
  inside the kernel (the book is already tables). This is the only change in sight that removes most of the loop's Python;
  it is a rewrite of the loop, and nobody has measured what it would give. Measure first (below).
- **Labour** (`year_labour.clear_labour`): the kernels (`switch_all`, `hire_markets`, `market_heads`, `settle_wage_markets`)
  are most of it; `Supply.reach_block` still calls `actor_staff_fte` (`sim/actors/staff.py`) and `agent_hours_offered_at`
  per trade (block views in the actors and markets modules are needed); `setup.labour_area` is asked tens of thousands of
  times from `land_lease_year._outside_options`; scalar `Supply` readers (`hands_available`) build a whole `PeopleByTile`
  for one tile.
- **Close** (`year_close.close_agents`): `ProducerColumns.of` (`year_arrays_producers.py`) is rebuilt several times a year
  after producer writes (needs the exit compaction row map to update in place); `producer_blocks._names_of` (its callers'
  id lists are not rows); `year_close_producers._share_pricer` calls `crossing_price.ColumnDemand.price_with_supply` one
  quantity at a time (a batch over many demand columns is not written); per-cohort and per-loan loops
  (`households_close.closed_figures`, `households_own.next_own_plan`, `households_close_pack.add`, `carriage_hours.wage_loans`,
  `merchants_news.lags_at`, `producer_close_write._write_crews`, `practice.crew_runs_after_year`, `_write_expected_prices`);
  the priced rows of a basket are rebuilt for each new hired-work floor key.
- **Household orders** (`year_order_sources.cohort_orders`): `households_orders_pack.add_template` (about two dozen small
  numpy calls per template; a template-level kernel is not written), `_store_weights` and `store_offers` (Python rules over
  dicts, `math.log`/`exp`/`fsum` that a kernel would have to reproduce to the last digit), the per-cohort loop's reads,
  `land_bids` and `tool_bids` return `Bid` objects.
- **Merchant orders**: `merchants_plan.orders` commit loop, `merchants_legs.from_weights`, `_Stock` per merchant;
  `carriage_fleet_book.bids` returns `Bid` objects.
- **Entry** (`entry_year.open_entrants`): a greedy loop where an earlier plan changes the capacity a later plan of the same
  producer reads (`producer_table.set_fields` inside it); `live_input_prices_at` and `live_wages_at` per producer (the
  market memory is written between the readers, so a per-write grid misses; a block read needs arrays threaded through
  `settle_year` -> `post_rents` -> `demands_of`).
- **Money phases outside the economy** (`year_steps.money_world`): the governments' and the registry's `advance`
  (`ActorRegistry.advance`, one Python method per actor that a mod's actor kind may override), `Government.pay_standing_need`,
  `budget.standing_lines`, `state_enterprises.run`. Not converted.
- **`dict.get`** is still the largest builtin of the profile (several hundred thousand calls); its callers are spread
  (`pstats` `print_callers('get')`).

## What to do next (recommendation)

1. **Measure the ceiling before rewriting.** For each phase above, its Python own time (split profile, the phase's
   cumulative minus its `kernel__` entries) is the most a rewrite of that phase can save. Add these up and check that the
   phases you plan to rewrite can reach one second together; then do the largest.
2. **Prototype the per-good kernel** (turn, clear, settle in one call per good with the book's columns) on one good's
   path behind a switch, compare it bit for bit with the current path on recorded inputs, and time the whole loop. Continue
   only if the loop's Python falls by most of its share.
3. Then the household orders template kernel, the close's per-cohort pass, and entry, each measured the same way.
4. Kernels last: `decide_markets` and `respend_rounds` only by algorithmic means that keep every answer bit for bit.

Stop a line of work that does not show in `warm_year_cpu.py`. Several packages of this branch removed thousands of calls
and saved nothing measurable.

## How to measure

- `python3 tools/measure/warm_year_cpu.py SAVE`: process time of one warm year (also counts `Producer` builds).
- `python3 tools/measure/warm_year_split_profile.py SAVE OUT.prof`: cProfile with each kernel as its own `kernel__` entry.
  **Plain cProfile (`warm_year_profile.py`) does not see calls into numba kernels: a kernel's time shows as its Python
  caller's own time.** Several targets of this branch were chosen from that misreading.
- `python3 sim/simulator.py year-time --session SAVE --years N --reload-check [--keep OUT] [--count-instructions]`: wall per
  year, the digest, save-and-load reproducibility; instruction counts under valgrind (load-independent, slow).
- `python3 tools/measure/function_times.py SAVE module:function ...`: plain timers around chosen functions.
- `python3 tools/measure/save_compare.py A.json B.json`: what differs between two stepped games.
- Wall time on a shared machine swings by more than most cuts: alternate base and branch three times each on the same load,
  both warm, and compare medians.

## How a change is checked (protocol used on this branch)

1. A test that calls the new function with written-out and seeded random inputs and compares bit for bit with the old
   path, kept as plain reference code in a test helper (`sim/tests/settlement_ids_plain.py`, `goods_good_plain.py`,
   `kernel_speed_plain.py` are the pattern).
2. `python3 sim/simulator.py compile-kernels; echo $?` is 0 (a kernel the fixture does not reach needs its signature in
   `sim/ui/kernel_signatures.py`, imported through the package's `api.py`; an unreached kernel makes it exit 1).
3. `python3 -m sim.tests` green, and `ROME_NO_JIT=1` on the topics covering new kernels.
4. `tools/check_table_names.py`, `check_package_walls.py`, `check_module_reads.py`, `check_record_owners.py` unchanged.
5. Digests unchanged where nothing is meant to move: `year-time` Rome two years and England five years with
   `--reload-check`, compared with the base's digests (record them on the base first).
6. A fresh spin-up: an empty `ROME_CACHE_DIR`, `python3 -m sim.tests --slow --jobs 1 --topic-seconds 700 --only
   protocol_golden`; its first-command values must equal the base's (saved games do not cover the opening).
7. `python3 -m sim.tests --slow --jobs 1 --only hash_seed_order` (string-hash order must not reach the game).
8. Process time, alternating base and branch.
9. Before a pull request: `--slow` on a checkout pinned to one commit.

## Traps (each cost hours on this branch or the port)

- **cProfile and numba** (above): use the split profile.
- **numba's cache and callees in other files.** numba checks only a kernel's own file. The cache directory is now named by
  a digest of the source (`sim/kernel_cache.py`): `ROME_KERNEL_CACHE_KEY=source` (default: games, `--slow`, checks before a
  pull request) covers every file under `sim/`; `=kernels` (the quick tier's default, and agents' edit-test loops) covers
  only files that define kernels and can miss a changed constant in another file. The first run after an edit compiles
  every reached kernel (minutes on four cores): never time that run.
- **The price-solve cache is keyed on source**, so the first run after any edit solves cold and distorts its profile.
- **Python's `sum()` compensates rounding for exact Python floats only**; numpy scalars take the plain path. A store that
  changes a field from `np.float64` to `float` moves last digits; a fresh spin-up amplifies a one-ulp move in a land rent
  into percent-level differences in capital and a different producer count. That is dust, not a rule change, but it hides
  real changes: compare fresh spin-ups between base and branch, not against stale goldens.
- **numpy `ndarray.sum` is pairwise** (blocks of eight running sums up to 128 terms, then halved); a kernel that must match
  it bit for bit reproduces that (`numpy_sum` in the settlement kernels). numpy's scalar `exp` and numba's differ in the
  last bit.
- **numba has no `lexsort`**: successive stable `argsort(kind="mergesort")` calls, least significant key first, give the
  same order including ties (`stable_order_kernel`).
- **Dict key order** reaches the game where a dict is iterated later: build dicts in the order the old loop first met each
  key.
- **A table class's name must equal its module attribute** (`TableSpec("Requests", ...)` held as `Requests`), or numba's
  cache never finds it and recompiles in every process (`tools/check_table_names.py`).
- **`check_record_owners.py` matches names**: a kernel's scratch table named `merchants` reads as the merchants record;
  name scratch tables otherwise (`merchant_rows`).
- **`protocol_golden` takes longer than its topic limit on a loaded machine**; a timeout shows as an extra failure.
- **Order must not depend on history** (CLAUDE.md): iterate in a load's order or sorted.
- The traps of the numba port (bounds not checked: run with `NUMBA_BOUNDSCHECK=1`; numpy scalars in records; caches keyed on
  a write stamp need every writer to bump; shipped openings go stale on economy edits) still hold.

## Working with agents on this

What worked: briefs that list the functions to convert with their call counts, the exact checks (as above) with the base's
digests and fresh spin-up values, the files other agents own, and "too large" or "budget" not accepted as a reason, only a
concrete technical one with its code line; agents report call counts and process time before and after. What did not:
large packages (agents run out of budget and stop at the first hard kernel), and choosing targets from plain cProfile.
Agents that run whole games compete for cores: no more at once than the machine has cores to spare.

## Related

Complaint 497 (speed history), 966 (the sample Egypt civilisation does not open), 967 (the test runner opens every
civilisation before a slow topic), 969 (a quick fingerprint scenario stops on an empty nation).
