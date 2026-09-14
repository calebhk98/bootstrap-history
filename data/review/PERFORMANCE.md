# PERFORMANCE.md - where a simulated year actually goes

The reported symptom: `python3 rome/sim/simulator.py run --civ rome_100ad
--strategy rome/sim/strategies/planned_rome.json --mc 3 --horizon 700` takes
between thirty minutes and two hours - 2,100 simulated years, roughly one to
three seconds of wall clock per year, for a model whose state is a few
thousand booleans and a few dozen floats. This is measured before any code
was touched, what it turned out to be, and what four small, independent
fixes bought, each verified deterministic and against the regression suite.

**Do not trust guesses about this codebase, including previous ones.** The
instructions that produced this document note that several confident wrong
diagnoses had already been offered today. What is below is a profile, not a
theory: `cProfile` over `Sim.run()`, single seed, single trial, 300
simulated years (100 AD -> 400 AD), `rome_100ad` on the `planned_rome`
strategy. That is the same shape of work the slow command does, at a
tenth of the length, and it is fast enough to iterate on directly - the
whole point of the ground rule against running `--mc` sweeps as a
measuring stick.

## The baseline profile (before any change)

```
71,471,967 function calls in 34.435 seconds   (300 simulated years, one seed)
```

By self time (`tottime` - time inside the function itself, not in what it calls):

| ncalls | self time | function |
|---:|---:|---|
| 1,546,809 | 7.142s | `economy.py:_goods_category_state` |
| 34,117,767 | 2.933s | `dict.get` |
| 28,423 | 2.399s | `economy.py:revenue` |
| 604,367 | 1.789s | `sorted` (builtin) |
| 25,819 | 1.330s | `economy.py:capability_factor` |
| 1,546,809 | 1.215s | `economy.py:_goods_category_ratios` |
| 300 | 1.151s | `core.py:step` |
| 1,420,076 | 1.103s | `economy.py:venture_ramp` |
| 21 | 0.830s | `core.py:1102` (`[k for k in self.order if k not in set(earners)]`) |

By cumulative time (`cumtime` - this function plus everything it calls):

| ncalls | cumtime | function |
|---:|---:|---|
| 28,423 | 21.861s | `revenue()` |
| 9,314 | 15.883s | `living_cost()` |
| 1,420,076 | 15.635s | `goods_market_factor(k)` |
| 4,615 | 11.745s | `credit_limit()` |
| 1,546,809 | 13.710s | `_goods_category_ratios(cat)` |
| 1,546,809 | 11.040s | `_goods_category_state(cat)` |

**The per-call counts are the number to read, not the cumulative times** -
a previous pass on this code found `revenue()` calling one helper 61
million times in a run, and the pattern here is the same shape: a handful
of top-level "what is my financial state" queries (`revenue`,
`living_cost`, `credit_limit`), each one fanning out into a million-plus
calls to a function that recomputes something from scratch that had
already been computed a moment earlier, or that cannot have changed since
the year began.

## What was actually being recomputed

### 1. `revenue()` called twice by its own caller, for no reason

`living_cost()` (economy.py) called `self.revenue()` once to compute
`tax`, and again eighteen lines later to compute `room` - with nothing in
between that mutates any state `revenue()` reads. `self.wage_bill()` had
the identical pattern. `revenue()` is not cheap (see below), so
`living_cost()` alone was responsible for roughly two of every three calls
to it (9,314 calls to `living_cost()` x 2 = 18,628 of `revenue()`'s 28,423
total calls). Every other caller of `living_cost()` - `net = (self.revenue()
- self.upkeep() - self.living_cost() - ...)`, all over core.py, labour.py,
projects.py, society.py - was therefore paying for revenue() three times
to get one number.

### 2. `_goods_category_state()`: `sorted(self.operating)`, scanned and
   filtered, on every single call

`goods_market_factor(k)` - called once per operating venture inside
`revenue()`'s main loop - asks `_goods_category_ratios(cat)` for its
node's category, which calls `_goods_category_state(cat)`. That function
did:

```python
for m in sorted(self.operating):
    if self.nodes[m].get("cat") != cat:
        continue
    ...
```

`self.operating` is the set of every concern the player currently runs, and
this sorted the whole thing and threw away every member that did not match
`cat`, on every call. Worse: for every venture in a *non-essential*
category, `goods_market_factor` also calls `income_factor()` ->
`essential_price_ratio()` -> the *same* `_goods_category_state()`, again,
for the essential category (`processing`). So the call volume is roughly
(operating ventures) x (operating ventures x categories touched) - the
quadratic-in-portfolio-size shape that made later, more-built-up years of
a run cost far more than early ones, and that a 700-year run (far more
built up by the end than a 300-year one) would hit far harder than this
profile shows. `cat` is fixed on a node at tree-load time and never
changes at runtime; nothing here needed re-deriving every call, let alone
every call for every operating venture.

### 3. `set(earners)` rebuilt from scratch, once per node, in `self.order`

In `step()`'s auto-start-work branch (core.py, ~line 1097), when money is
tight relative to fixed costs:

```python
candidates = earners + [k for k in self.order if k not in set(earners)]
```

`self.order` carries the strategy's full working order - 2,833 nodes for
`planned_rome`. Because `set(earners)` is written inline inside the
comprehension's condition, Python rebuilds it from scratch on every one of
those 2,833 iterations: an O(|order| x |earners|) rebuild of a set whose
contents never change during the walk, where one set built once would
cover the whole thing in O(|order|). This branch is rare early in a run
(21 calls in this 300-year profile) and far more common whenever revenue
stays tight for a long stretch - exactly the condition a 700-year run
spends more of its time in.

### 4. `material_price_factor()`: the whole tick's demand dict, scanned
   per material, per node

```python
for (ek, tag), need in sorted(self._cached_demand_by_tag().items()):
    if ek != emp_key or need <= 0:
        continue
    ...
```

`_cached_demand_by_tag()` is already a proper per-tick cache (see its own
comment in economy.py, and `resource_throttle()`'s). But
`material_price_factor(emp_key)` re-sorted and re-scanned that whole dict
and threw away everything not matching `emp_key`, on every call -
`project_cost()` calls it once per material a candidate node buys, once
per candidate node, every year.

### What did *not* need fixing

`_done_seq` (economy.py's existing `_done_changed()` convention) and the
per-tick material-demand caches (`_material_demand_cache`,
`_demand_by_tag_cache`) were already doing the right thing before this
pass, and the fixes below reuse those exact conventions rather than
inventing a second caching scheme. `labour.py`'s `auto_commission_for_blocked`
memoizes `market_supply`/`trade_available` per call with a local dict
already (`_ms_memo`, `_ta_memo`), correctly hoisted outside the
2,800-iteration loop - also not touched.

## The fixes, in the order they were made, and what each measured

All four fixes are in economy.py or core.py, each its own commit, each
re-profiled, re-run against the regression suite
(`rome/sim/test_regressions.py`, 860 checks), and checked for determinism
(same seed, separate processes, and under different `PYTHONHASHSEED`
values, output diffed byte-for-byte) before being called done.

| # | Fix | ncalls before -> after (300yr profile) | Cumulative profiled time (300yr) |
|---|---|---|---|
| 1 | `living_cost()`: call `revenue()`/`wage_bill()` once, reuse | `revenue()` 28,423 -> 19,109 | 34.4s -> ~27s |
| 2 | `_goods_category_state()`: static per-category node index instead of `sorted(operating)` per call | `_goods_category_state` 1,546,809 -> 1,039,683 calls, self time 7.142s -> 1.587s | ~27s -> 21.5s |
| 3 | `core.py`: hoist `set(earners)` out of the per-node comprehension | the 0.811s/21-call line no longer appears in the top 35 by self time | 21.5s -> 21.2s (this branch is rare at horizon 300; see below) |
| 4 | `material_price_factor()`: group per-tick demand by `emp_key` once, cached the same way `_cached_demand_by_tag()` already is | `material_price_factor` no longer re-sorts the full demand dict per call | 21.2s -> ~20.0s |

Total for the 300-year single-seed profile: **34.4s -> ~20.0s under the
profiler**, function calls **71.5M -> 39.1M**. The profiler itself adds
substantial overhead (instrumenting every call), so the un-profiled wall
clock moved by more in relative terms:

```
python3 rome/sim/simulator.py run --civ rome_100ad \
  --strategy rome/sim/strategies/planned_rome.json --mc 1 --horizon 300 --seed 1

before:  12.134s
after:    6.563s     (1.85x)
output: byte-for-byte identical
```

**The clearest evidence is on the actual reported shape of the problem**
- single seed, `--horizon 700`, no `--mc` (per the ground rule against
running MC sweeps as a measuring stick):

```
before (baseline, un-optimized): did not finish inside a 600s (10 minute)
                                  timeout - killed, still running
after (all four commits applied): 3m26s (206s), completed, reached
                                  point_contact_transistor as first blocked node
```

That the baseline did not even finish a *single* 700-year seed within ten
minutes, while the reported symptom is 3 seeds in thirty minutes to two
hours, is consistent with fix #2 and #4's quadratic-shaped costs: a
700-year run has a far larger `operating` set and far more material
pressure late in its life than a 300-year one, so the per-call cost those
two fixes removed was growing with it, not staying flat. This is also why
fix #3's measured effect looks small at horizon 300 (21 calls) - the
branch it fixes fires when revenue is tight relative to fixed costs, which
is rare early in a short run and the norm in a long, materially-constrained
one.

## Determinism

Per fix, and cumulatively: the same seed, run in separate processes, and
under `PYTHONHASHSEED=1`, `999`, `555`, `777` (arbitrary distinct values),
produced byte-for-byte identical stdout, both against each other and
against the un-optimized baseline's own output for the same seed. No cache
added here changes the iteration order of anything that feeds a float sum:
`_goods_category_state`'s new per-category index and `material_price_
factor`'s new per-key grouping are both consumed only by `max()` (order-
independent), and the `_goods_by_cat`/`_demand_by_emp_key` caches are
built from `self.nodes.items()` / an already-existing dict, both of which
iterate in insertion order regardless of `PYTHONHASHSEED`.

## What is left on the table, and why it was not done here

The dominant remaining cost by self time is still inside `revenue()`'s own
loop (`goods_market_factor`, `venture_ramp`, `_goods_category_ratios`) and
`capability_factor()`, both of which walk `done_in_order()` - every
completed node - on every call, filtering for what is or is not currently
`operating`/`granted`. `capability_factor()` in particular sums over the
full done list every one of its ~17,000 calls in this profile, and its
result changes only when `self.done` or `self.operating` changes, not
every call. Making that properly incremental (an accumulator maintained
alongside `self.done`/`self.operating`, rather than a full walk) would
plausibly be the next-largest win, but `self.operating` is mutated directly
(`.add`/`.discard`) from nine call sites across core.py, projects.py,
economy.py and society.py - four files, all being edited by other agents
concurrently right now. Wiring in a correct invalidation signal that
does not go stale means touching all nine, and getting that wrong
silently changes results rather than just slows them down. That is an
architectural change - a real accumulator with a real invalidation
contract, not a one-line cache - and it is recommended, but not attempted
in this pass, in favour of leaving four small, independent, easily-rebased
commits behind instead of one large one that conflicts with everybody.

## Addendum: `capability_factor()`, made incremental-by-invalidation

A later pass picked this up once core.py, projects.py, economy.py and
society.py were no longer being edited concurrently. Same method as
above throughout: `cProfile` over `Sim.run()`, single seed, single trial,
300 simulated years, `rome_100ad` on `planned_rome`, plus un-profiled wall
clock on the same run, plus a single `--horizon 700` seed (no `--mc`, per
the ground rule against sweeps) for the shape of the actually-reported
problem.

### The invalidation contract

`self.done` already has one: `_done_changed()`, called by hand at every
site that adds to or removes from `self.done`, clearing `self._done_seq`
(`done_in_order()`'s cache). `self.granted` needed no separate signal: every
site that adds to `self.granted` does so in the same breath as adding to
`self.done` and calling `_done_changed()` (core.py x2, society.py x1 -
checked by reading all three), and nothing ever removes from `granted`, so
`_done_changed()` already covers it.

`self.operating` had no signal at all, and is mutated (`.add`/`.discard`)
from ten call sites, not nine as the estimate above had it - core.py (2),
projects.py (5), economy.py (2), society.py (1) - plus three places that
replace it wholesale (`self.operating = X`): a fresh `Sim.__init__`,
`load_state`'s generic `setattr` loop, and one test.

Two shapes were tried.

**First: a property.** `self.operating` became a property backed by an
`_InvalidatingSet` (a `set` subclass that calls a callback on every
mutating method - `add`, `discard`, `remove`, `pop`, `clear`, `update`,
`difference_update`, `intersection_update`, `symmetric_difference_update`,
and the in-place operators), with the property's setter re-wrapping
whatever was assigned so that whole-object replacement - `load_state` in
particular - kept invalidating too. This is the same pattern `revealed`
(engine/fog.py) already uses, for the same reason (a ratchet there, an
invalidating cache here), and it is correct: every one of the nine-or-ten
mutation sites started invalidating the cache automatically, with nothing
added to any of them.

Measured, it made the profiled run slower, not faster: **22.1s -> 27.5s**,
44.2M -> 60.4M calls. `self.operating` turned out to be read - membership
tests, iteration, `sorted(...)` - roughly **16.2 million times** in this
one 300-year run (`_goods_category_state` and `goods_market_factor` alone
account for most of that; `_goods_category_state` is fix #2 from the
section above, and it is exactly as hot now as it was then). A property
intercepts every one of those reads to protect a few thousand writes a
run; the interception cost, paid 16.2M times, was far larger than what
caching `capability_factor()` saved. Read `_operating_changed()`'s comment
in economy.py for the full account - it is left in the source because the
next person to reach for "just make it a property" should see the number
that made this one turn back.

**Second, and what is actually committed: a plain attribute holding an
`_InvalidatingSet`.** Reads are exactly as fast as a plain `set` - `in`,
iteration, `sorted()`, truthiness are the base class's own C-level methods,
inherited unchanged, with no Python-level interception at all. Only the
nine-or-ten call sites that actually mutate it pay anything, and what they
pay is one attribute lookup and a comparison (`_fire()` only calls the
callback when membership actually changed), a few thousand times a run.

That leaves exactly the gap the property closed and the plain attribute
does not: whole-object replacement. `Sim.__init__` needs nothing (there is
nothing yet to invalidate). `load_state`'s generic `setattr(s, f, v)` loop
(protocol.py) is the real one, and it is not always acting on a
freshly-constructed `Sim` - `load` issued mid-session through the
agent/play JSON protocol runs it against the *same* long-lived object a
player goes on playing in, not a new one, so a `setattr` that silently
downgrades `self.operating` to a plain, non-invalidating `set` would stay
broken for the rest of that process's life, the first time anything after
that `load` opened or closed a concern. `Sim._reset_operating()` closes
that one door explicitly - re-wrap in a fresh `_InvalidatingSet`, invalidate
once - called once from `load_state` right after its generic loop, instead
of taxing sixteen million reads to guard a gap with exactly one entrance.

`_done_changed()` was extended by one line (`self._cap_factor = None`) to
invalidate `capability_factor()`'s cache too, since that function also
filters by `self.done`/`self.granted`; a parallel `_operating_changed()`
does the equivalent for `self.operating`, called automatically by the
`_InvalidatingSet`, by nothing else, and by hand nowhere.

### Why the cache holds a recomputed result, not a running total

`capability_factor()` sums `n["rev"] * (1.0 + 0.25 * n["tier"])` over
`done_in_order()` (a list, fixed order - this was already cached and
already deterministic before this pass), filtered by `self.granted`/
`self.operating`. An accumulator that added a node's weight in when it
entered the sum and subtracted it when it left would be faster still, and
was rejected: float addition is not associative, and the order nodes
enter or leave `self.done`/`self.operating` at runtime (a tech finishing,
a venture closing and later reopening, a sacking) is not the order
`done_in_order()` walks them in. An incrementally-maintained total would
therefore drift from a full recompute in its last bits over a long run -
a behaviour change, not merely a speed one, exactly the risk the
instructions for this pass called out by name. The cache instead holds the
*result* of calling the exact same loop, in the exact same order, with the
exact same arithmetic, recomputed whole on invalidation - bit-identical to
calling the uncached version every time, by construction, while still
turning ~17,000 calls into however many times `self.done`/`self.operating`
actually change in a run (665 `_operating_changed` + 514 `_done_changed` =
1,179 in this 300-year profile, not 17,000).

### Profile: before -> after (300 simulated years, single seed)

| | before | after |
|---|---:|---:|
| total calls | 44,215,157 | 44,200,317 |
| total time (profiled) | 22.086s | 21.374s |
| `capability_factor()` calls | 18,673 | 18,673 |
| `capability_factor()` self time | 1.129s | 0.095s |
| `capability_factor()` cumulative | 1.139s | 0.098s |
| `_operating_changed`/`_done_changed` calls | - | 665 / 514 |

`capability_factor()`'s own self time fell 92%; everything else in the hot
path (`_goods_category_state`, `_goods_category_ratios`,
`goods_market_factor`, `venture_ramp`, `credit_limit`, `living_cost`) is
unchanged within measurement noise - this fix touches only
`capability_factor()` and `self.operating`'s mutation sites, nothing it
calls or is called by. Total call count barely moved (14,840 fewer calls,
the difference between 18,673 cache-recomputes-that-would-have-happened
and 1,179 that actually did, each one a handful of list/dict operations),
which is the clearest evidence the plain-attribute `_InvalidatingSet`
route has none of the property's per-read tax: nothing got cheaper to call
that wasn't meant to, and nothing got more expensive either.

Unprofiled wall clock, `simulator.py run --civ rome_100ad --strategy
rome/sim/strategies/planned_rome.json --mc 1 --horizon 300 --seed 1`,
mean of 3 runs each:

```
before: 7.45s
after:  7.20s      (~3.4% faster)
```

On the actual reported shape of the problem - single seed, `--horizon
700`, no `--mc`:

```
before: 131.3s, 150.1s   (mean 140.7s)
after:  140.2s, 130.8s   (mean 135.5s)
output: byte-for-byte identical in every run, before and after
```

This pair is noisy - the machine was shared with other agents running
simulations concurrently throughout this measurement, per this project's
own ground rules, and a single 700-year run is long enough (2-2.5 minutes)
for that contention to swing a result by ten or more seconds either way,
which is larger than this fix's true effect at this tree size. The mean
across two runs each still lands in the same ~3-4% direction as the
tighter, lower-noise 300-year measurement (3 repetitions, small spread);
neither pair is large enough on its own to prove a precise percentage at
horizon 700, but both agree on the sign. This fix was always expected to
be smaller than the four it follows: the profile at the top of this
document already shows `capability_factor()` at 1.1s of a 22s run, not the
multi-second, quadratic-shaped costs fixes #2 and #4 removed - "plausibly
the next-largest win" is what the closing section above called it, and a
few percent on top of an already-fixed run is what it turned out to be.

### Determinism

Same seed (`--seed 1`), `--horizon 300`, run in separate processes under
`PYTHONHASHSEED=1`, `999`, `555`, `777`, before this pass's changes and
after: all six stdouts are byte-for-byte identical -
md5 `2ec62257b694b65387edf6cb878fc2b3` in every case. The `--horizon 700`
runs above were also diffed byte-for-byte against each other (before vs.
after) and are identical despite the ten-digit swing in wall clock. No
cache added here changes the order anything is summed in:
`capability_factor()`'s cache holds the finished result of the same
`done_in_order()` walk the uncached version did, not a total built by
adding and subtracting pieces in a different order (see above).

### What is still left on the table

`revenue()`'s own loop still walks `done_in_order()` once per call,
calling `venture_ramp()` and `goods_market_factor()` for every operating
node every time - that part was deliberately not touched here, and is not
simply cacheable the way `capability_factor()` was: `venture_ramp(k)`
depends on `self.year` (it changes every single simulated year by
definition, ramping a concern up over its first few years) and
`goods_market_factor(k)` depends on the *whole current `operating` set in
`k`'s category* (market saturation - opening a second concern in the same
category changes the first one's figure too), not on `self.done`/
`self.operating` membership alone. A cache keyed the way
`capability_factor()`'s is would be wrong on any year nothing in `done`/
`operating` changed but the calendar or a competing venture did - which is
most years - the same trap `PERF_AUDIT.md` already declined for
`start_reason`/`can_start`, for the identical reason. Revisiting that
would need a cache keyed on `(self.year, frozenset of that category's
operating members)` or similar, which is a real multi-key invalidation
design, not a one-line extension of this one, and was left alone rather
than risk getting a correctness-sensitive key wrong under the same
instruction that governed this whole pass.
