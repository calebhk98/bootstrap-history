# The same simulation, run twice, gives two different answers

**Type:** Correctness / determinism
**Priority:** Blocking
**Status:** FIXED. Root cause and fix are at the bottom of this file.

Everything between here and `# RESOLVED` is kept exactly as it was written
during the investigation, wrong guesses included - the `## Ruled out` entry
that cleared the very cache responsible, and the `## Expected behavior`
section predicting the fix would be "whatever makes the order deterministic",
which is not what it was. How this went wrong is worth more than the fix, and
editing it into hindsight would throw that away.

## The concern

`sim/perf_fingerprint.py` is the tool `sim/ARCHITECTURE.md` names as the way to
prove a change altered nothing. It does not reproduce its own recording.

On a pristine checkout with no local changes:

| What was run | Result |
|---|---|
| `record`, then `check` against the same checkout | `FAIL: 2 of 9 scenarios diverged` (rome/seed1 at year 106, england/seed1 at year 97) |
| `record` twice, diff the two recordings | 1 of 9 diverged (mexica/seed1 at year 7) |

Same code, same seeds, same machine, minutes apart. A different scenario and a
different year every time.

## Why it matters

Two reasons, and the second is the serious one.

**The safety net is not a net.** `sim/ARCHITECTURE.md` is explicit that the
test suite does not prove behaviour unchanged and that `perf_fingerprint.py`
is what does. Right now a clean `check` proves nothing and a dirty one accuses
nothing, so no refactor of the simulation loop can be verified. That blocks
the actor/ownership work the architecture plan depends on.

**It is not only the tool.** Something in this engine returns a different
answer for the same inputs. A simulator whose costs are supposed to be
calculated rather than looked up cannot have arithmetic that depends on the
memory allocator.

## Reproducing it

`python3 sim/repro_nondeterminism.py` turns a twenty-minute, never-the-same-way
failure into about ten seconds. One scenario, four runs, one process, same
seed, nothing changed in between:

```
run 1  7d77685af3129077        run 1  d35355f9c94e35a8
run 2  d35355f9c94e35a8        run 2  d35355f9c94e35a8
run 3  d35355f9c94e35a8        run 3  7de0c8b0741215f5
run 4  d35355f9c94e35a8        run 4  d35355f9c94e35a8
```

Two invocations, minutes apart. Which run is the odd one out changes; that
there is one is reliable. It is sporadic rather than ordered, so "the first
run is different" - the obvious first guess, and one that two separate
observations appeared to support - is wrong.

`--bisect` names the damage. On rome_100ad/seed1 the first difference is at
year index 18, in one field of one project:

```
potash_soda  ph_left   A=152.51383869514427  B=152.51383869514555
```

1.3e-12, in the last bits of a float. That is the signature of the same sum
taken in a different order, and `economy.done_in_order()`'s own docstring
describes the exact failure and what it costs:

> floating point addition is not associative, so the totals differed in their
> last bits between one process and the next. Over five hundred years those
> last bits decide which side of a threshold you land on, and the same --seed
> gave two different answers on alternate invocations.

That was found and fixed in three places. This is a fourth, somewhere else.

## Ruled out

Recorded so the next person does not spend the afternoon twice.

- **Hash-seed randomisation.** One scenario alone in a fresh process gives a
  byte-identical digest over three runs with `PYTHONHASHSEED` unset and three
  with it fixed at 0.
- **Mutation of the shared tree.** `NODES` and `ORDER` hash identically before
  and after six scenarios run against them.
- **Module-level state.** No container in `data`, `economy`, `labour`,
  `projects`, `society`, `geography`, `fog`, `commodities` or `proto.nodes`
  changes content across a run. No `Sim` class attribute is created or mutated
  anywhere in the MRO except the three below.
- **The `CommodityLedger` accumulating state.** Read-only in practice: none of
  its four attributes changes across a 60-year run.
- **The `id()`-keyed cache in `_revenue_upkeep_candidates`** (`economy.py`
  ~2110). The best-looking hypothesis: `id()` is a memory address, a freed
  object's address is reusable, and `sim/engine/proto/nodes.py` documents that
  exact hazard and defends against it by holding a strong reference, while the
  three other `id()`-keyed caches in the engine do not. A probe recomputing
  the true answer on every call found **0 stale answers in 64,157 calls**.
- **The `id()`-keyed `_demand_by_tag_cache`** (`economy.py` ~3319), for a
  duller reason: it hits three times in four 80-year runs.

Both probes allocate, and allocation is exactly what the suspected hazard
depends on, so neither is a clean bill of health. `_DESC_CACHE` in `data.py`
~285 - keyed on `id(nodes)` and validated only by `len(nodes)` - has not been
examined.

## Where it stands

`python3 sim/repro_nondeterminism.py --caches` shows the only cross-`Sim` state
found: three caches on `EconomyMixin` (`_commod_ledger_cache`,
`_material_commod_map_cache`, `_material_prices_cache`), `None` before the
first run and shared by every `Sim` afterwards. Clearing them between runs
changes the answer, so they are implicated. They are also built
deterministically from JSON in file order and never mutated, so they cannot be
changing a sum directly. The likeliest reading is that constructing them
perturbs allocation and something downstream is sensitive to that, which is
another way of saying there is still an order-dependent float sum nobody has
found.

## Expected behavior

Running the same scenario with the same seed returns the same answer, in the
same process or a different one, whatever has run before it. When it does,
`sim/repro_nondeterminism.py` becomes a regression check in `sim/tests/`.

The fix is whatever makes the order deterministic at the offending site -
sorting before summing, or iterating a list rather than a set - matching what
`done_in_order()` already does for the three sites found previously.


---

# RESOLVED

## What it was

An `id()`-reuse hazard, in the second of the two caches this file's
`## Ruled out` section had dismissed.

`_cached_demand_by_tag()` and `_demand_by_emp_key()` in `sim/engine/economy.py`
both cached their result keyed on `id(demand)`, where `demand` is the Counter
`annual_material_demand()` returns. That Counter is a brand-new object every
call, and the old one is dropped the moment `resource_throttle()` overwrites
`self._material_demand_cache` with next year's. CPython hands a freed small
object's address to the very next same-sized allocation often enough that a
later tick's Counter regularly landed at the exact address an earlier tick's
had. `cached[0] == id(demand)` then read true for two genuinely different
ticks, and the cache replayed a stale material-demand grouping under a fresh
year.

That path is hot: `material_price_factor()` -> `material_market_factor()` ->
`project_cost()`, which is what sets a project's `ph_left`. Hence the symptom -
last-bit float differences in `ph_left`, sporadic, because whether the address
gets recycled depends on the process's entire allocation history rather than on
anything in the simulation.

## The fix

The defence `sim/engine/proto/nodes.py` already documents for the identical
hazard: hold a **strong reference** to the object in the cache entry and
compare with `is`, rather than comparing two bare integers. Keeping the old
Counter alive for as long as the entry might be checked against it means its
address cannot be recycled into a false match. The collision becomes
structurally impossible rather than unlikely.

Two call sites in `sim/engine/economy.py`. No arithmetic changed.

A version-counter fix was tried first - a monotonic `_material_demand_ver`
bumped inside `annual_material_demand()`, by analogy with `_operating_ver`. It
also removed the non-determinism and was rejected because it broke
`sim/tests/test_literacy_market_pricing.py`, whose two pinned-demand checks
deliberately assign `s._material_demand_cache = {...}` directly. A version
counter cannot see that write; a fresh dict literal is a fresh object, so the
`is` comparison handles it correctly.

## Why the investigation went wrong, which is worth more than the fix

This file's `## Ruled out` section confidently cleared
`_demand_by_tag_cache` on the grounds that it "hits three times in four
80-year runs. It is not a hot enough path to matter."

That measurement was produced by a probe that built a signature tuple of the
whole demand dict on every call. The probe's own allocations were exactly what
stopped addresses being recycled - so it suppressed the effect it was measuring
and then reported the absence as evidence. The three hits it saw were the
legitimate ones; the false hits it existed to find could not occur while it was
watching.

The caveat was written down at the time ("both probes allocate, and allocation
is exactly what the suspected hazard depends on, so neither is a clean bill of
health") and then not acted on. Recording it plainly because the lesson
generalises: **when instrumenting a bug whose mechanism is allocation, the
instrument is part of the experiment.**

The test that did settle it allocates nothing extra: `del sim; gc.collect()`
before building the next `Sim` made two otherwise-diverging runs agree. Nothing
but an `id()` collision explains that.

## Verification

- `python3 sim/repro_nondeterminism.py --runs 15`, five separate processes:
  75 runs, zero divergence. Before the fix, four runs usually diverged.
- `python3 sim/perf_fingerprint.py record` then `check` against the same
  checkout: all nine reference scenarios identical. This is the property that
  was failing two of nine.
- Full suite green; `validate` clean.
- `sim/tests/test_determinism.py` now fails if it returns.
