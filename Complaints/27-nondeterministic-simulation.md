# The same simulation, run twice, gives two different answers

**Type:** Correctness / determinism
**Priority:** Blocking

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
