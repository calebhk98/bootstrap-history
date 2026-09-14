# Performance audit: the per-step optimizer loop

## Method

Profiled 150 steps of a non-manual (optimizer) `rome_100ad` run, seed 1,
`events=False`, under `cProfile`, built the same way `test_regressions.py`'s
`sim()` helper does (`S.Sim(NODES, ORDER, random.Random(1), events=False,
manual=False, civ=S.load_civ("rome_100ad"))`). Sorted by cumulative time, by
total (self) time, and by call count. Repeated for `han_china_100ad` to check
the fix generalizes to a civilization that isn't Rome (several of the hot
functions short-circuit specifically for `civ.id == "rome_100ad"`).

The profiling script is `/tmp/.../scratchpad/profile_run.py` (this session's
scratch directory; not committed). A separate, un-instrumented timing script
(`time_run.py`, same directory) was used for the wall-clock/CPU-time speedup
numbers, because `cProfile`'s per-call overhead itself scales with call count
and would have exaggerated the "before" number.

## Before: every function called > 1,000 times in 150 steps (rome_100ad)

11,589,923 total calls, 6.2s wall under the profiler. Sorted by call count;
`builtins.*` and dict/str methods included for completeness, commented out
reasoning follows below.

| calls | self(s) | cum(s) | us/call(self) | function |
|---|---|---|---|---|
| 2,052,756 | 0.202 | 0.202 | 0.10 | `dict.get` |
| 1,237,425 | 0.179 | 0.190 | 0.14 | `projects.running` |
| 891,821 | 0.259 | 1.915 | 0.29 | `core.py:741 <genexpr>` (the `_gone(t) for t in n["lab"]`) |
| 798,014 | 0.083 | 0.083 | 0.10 | `builtins.getattr` |
| 792,622 | 0.128 | 0.128 | 0.16 | `labour.trade_available` |
| 498,291 | 0.248 | 1.666 | 0.50 | `core.py:737 _gone` |
| 462,591 | 0.086 | 0.086 | 0.19 | `builtins.min` |
| 453,919 | 0.044 | 0.044 | 0.10 | `builtins.len` |
| 424,650 | 0.098 | 0.125 | 0.23 | `society._is_foreign_institution` |
| 411,685 | 0.102 | 0.143 | 0.25 | `fog.is_visible` |
| 399,169 | 0.143 | 2.036 | 0.36 | `builtins.any` |
| 294,358 | 0.035 | 0.035 | 0.12 | `str.lower` |
| **293,961** | **0.884** | **1.423** | **3.01** | **`labour.market_supply`** |
| 283,127 | 0.082 | 0.111 | 0.29 | `data.trade_family` |
| 244,588 | 0.028 | 0.028 | 0.11 | `dict.items` |
| **221,487** | **0.758** | **1.638** | **3.42** | **`projects.start_reason`** |
| 219,262 | 0.137 | 0.183 | 0.63 | `society.needs_first` |
| 219,262 | 0.072 | 0.093 | 0.33 | `society._is_foreign_only` |
| 219,262 | 0.153 | 0.153 | 0.70 | `projects.py:788` (`missing = [p for p in n["pre"] if p not in self.done]`) |
| 215,171 | 0.033 | 0.033 | 0.15 | `str.join` |
| 213,172 | 0.149 | 0.291 | 0.70 | `projects.py:795` (`known = [p for p in missing if is_visible]`) |
| 136,870 | 0.025 | 0.025 | 0.18 | `builtins.max` |
| 107,491 | 0.113 | 0.113 | 1.05 | `economy.py:973 <genexpr>` (upkeep's sum) |
| 79,941 | 0.062 | 0.091 | 0.78 | `economy.venture_ramp` |
| 51,014 | 0.054 | 0.078 | 1.06 | `labour.literacy_factor` |
| 39,925 | 0.018 | 0.022 | 0.45 | `projects.is_venture` |
| 23,619 | 0.024 | 0.184 | 1.02 | `builtins.sum` |
| 17,966 | 0.006 | 0.019 | 0.31 | `economy.done_in_order` |
| 17,222 | 0.011 | 0.016 | 0.66 | `economy._practice_set` |
| 13,945 | 0.007 | 0.010 | 0.49 | `labour.labour_pressure` |
| 13,930 | 0.017 | 0.115 | 1.23 | `labour.labour_price_factor` |
| 11,271 | 0.008 | 0.008 | 0.72 | `labour.director_pool` |
| 10,686 | 0.013 | 0.026 | 1.25 | `economy.practice_attention` |
| **10,540** | **0.241** | **0.412** | **22.85** | **`economy.revenue`** |
| 10,540 | 0.007 | 0.021 | 0.66 | `economy.workshop_output` |
| 10,540 | 0.004 | 0.006 | 0.38 | `economy.state_funding` |
| 7,723 | 0.002 | 0.002 | 0.26 | `labour.effective_scholars` |
| 7,680 | 0.004 | 0.004 | 0.52 | `dict.update` |
| 7,680 | 0.017 | 0.033 | 2.14 | `society.state_interest` |
| 6,978 | 0.016 | 0.133 | 2.35 | `labour.wage_bill` |
| 6,903 | 0.001 | 0.001 | 0.17 | `labour.py:913 <genexpr>` |
| 6,710 | 0.001 | 0.001 | 0.12 | `list.append` |
| 6,682 | 0.009 | 0.145 | 1.33 | `economy.upkeep` |
| 6,671 | 0.010 | 0.016 | 1.47 | `labour.craft_hands_available` |
| 6,090 | 0.008 | 0.011 | 1.35 | `projects.substitution_quality` |
| 5,845 | 0.001 | 0.001 | 0.22 | `core.has` |
| 4,887 | 0.002 | 0.028 | 0.49 | `projects.can_start` |
| 4,149 | 0.001 | 0.001 | 0.24 | `economy.cost_money_factor` |
| 4,140 | 0.009 | 0.016 | 2.25 | `society.civ_cost_factor` |
| 4,140 | 0.011 | 0.097 | 2.66 | `economy.project_cost` |
| 4,140 | 0.004 | 0.021 | 0.87 | `economy.opposition_factor` |
| 4,140 | 0.002 | 0.002 | 0.39 | `geography.material_cost_factor` |
| 4,140 | 0.002 | 0.002 | 0.36 | `society.py:399 <listcomp>` |
| 4,140 | 0.009 | 0.046 | 2.05 | `economy.material_market_factor` |
| 3,943 | 0.003 | 0.004 | 0.85 | `projects.venture_hands` |
| 3,414 | 0.018 | 0.488 | 5.36 | `economy.living_cost` |
| ... (30 more functions between 1,000 and 3,414 calls each; see the live profiler run for the complete list - `builtins.isinstance`, `economy.chosen_fuel`, `society.mult`, `economy._material_market_tonnes`, `builtins.sorted`, `economy.material_price_factor`, `labour._staff_advice`, `core.py:1280 <genexpr>`, `economy.credit_limit`, `economy.revenue_capacity`, `economy.mine_operating_cost`, `projects.py:381 <genexpr>`, `projects.venture_capex`, and others, none individually above 1% of total time) | | | | |

80 functions total cleared the 1,000-call bar. `han_china_100ad` produces the
same shape but with ~19.5M total calls instead of 11.6M for the same 150
steps, because the foreign-institution string search (below) is not a no-op
there the way it is for Rome.

## Root cause

Two call sites in `step()` are responsible for the overwhelming majority of
the calls above, and both walk the **entire** 2,831-node tree (`self.order`)
**every single year**, for the life of a 500-700 year run:

1. **core.py "4a", the ambient-institution auto-grant loop** (`for k in
   self.order: ... if self._is_foreign_institution(k): ...`). This calls
   `_is_foreign_institution` once per node per year regardless of whether
   the node could ever be granted this way - 2,831 x 150 = 424,650 calls in
   this run alone, and the function's answer is **completely static**: it
   depends only on `self.civ["id"]` (fixed at construction) and the node's
   own key/name (fixed tree data), neither of which ever changes after the
   `Sim` is built. The loop also only cares about a small, fixed subset of
   nodes (`tier==0, ph==0, _total_cost<=1`, not foreign) - of the 2,831
   nodes only **130** ever qualify.

2. **core.py "4a2", the auto-train loop** (`for k in self.order: ... def
   _gone(t): return not self.trade_available(t) or (self.market_supply(t)
   <= 0.0 and ...)`). `market_supply`/`trade_available` are pure functions
   of a handful of things (staff counts, taught trades, a few running()
   checks) that this block only *reads* - but they were being recomputed
   from scratch for every `(node, lab-trade)` pair. With `engineer`,
   `machinist`, `chemist` and `optician` absent from Rome for long
   stretches of the run, hundreds of nodes list one of those trades, so the
   same handful of distinct trade names were recomputed hundreds of times
   per year: 293,961 calls to `market_supply` and 792,622 to
   `trade_available` over 150 steps, cascading into 1,237,425 calls to
   `running()` and 283,127 to `trade_family()` underneath them.

The known example from the task brief - `revenue()`'s helper being called
~61M times - turned out to already be fixed in this codebase: see
`economy.py`'s `_practice_set()` (line ~949), whose own docstring describes
exactly that bug and its fix (a cache keyed on `len(self.granted)`, since
`granted` only grows at setup). `_practisable` itself was not a hot function
in this profile (17,222 calls to `_practice_set`, cheap). So the two items
above are the *next* instances of the same pattern.

`start_reason` (221,487 calls, 1.638s cumulative) and `market_supply`
(293,961 calls) are each called from several places, not only the loop
that names them in a comment, and legitimately need to be recomputed often
because `start_reason`'s answer depends on money, staff levels, arrears and
reputation - all of which can change every year even when `self.done` does
not. **I deliberately left `start_reason` itself uncached** (see "not
applied", below).

## Changes made

All three changes are in `rome/sim/engine/core.py` and
`rome/sim/engine/society.py`. None touch float summation order; none
iterate an unsorted set; none change what gets cached *across* a run in a
way that could go stale.

### 1. `society._is_foreign_institution` / `_is_foreign_only`: cached forever, never invalidated

```python
def _is_foreign_institution(self, k):
    if self.civ.get("id") == "rome_100ad":
        return False
    cache = self.__dict__.setdefault("_foreign_institution_cache", {})
    v = cache.get(k)
    if v is None:
        hay = (k + " " + self.nodes[k].get("name", "")).lower()
        v = any(m in hay for m in self.FOREIGN_MARKERS)
        cache[k] = v
    return v
```
(`_is_foreign_only` mirrors this with its own cache dict and
`FOREIGN_INSTITUTIONS`.)

**Keyed on:** `k` alone. **Invalidated:** never - by design, because
nothing it reads can change after construction:
- `self.civ["id"]` is set once at `Sim.__init__` and never reassigned
  anywhere in the engine (checked: no `civ["id"] =` or `.civ["id"]=`
  anywhere in `engine/*.py`).
- `self.nodes[k]["name"]` is tree data loaded once by `data.load()` before
  any `Sim` exists, and never reassigned (checked: no `["name"] =`
  anywhere in `engine/*.py`).
- The Rome branch is kept *outside* the cache on purpose: for
  `rome_100ad` the original one-line check (`civ.get("id") ==
  "rome_100ad": return False`) was already about as cheap as a Python
  call can be, and adding a dict lookup in front of it would be a net
  loss there while only non-Rome civilizations pay for the string search
  this replaces.

### 2. `core.step()`, section 4a: scan 130 candidates instead of 2,831 nodes

Added a lazily-built, permanently cached list:

```python
cand = getattr(self, "_auto_grant_candidates", None)
if cand is None:
    cand = self._auto_grant_candidates = [
        k for k in self.order
        if not self._is_foreign_institution(k)
        and self.nodes[k]["tier"] == 0 and self.nodes[k]["ph"] == 0
        and self.nodes[k]["_total_cost"] <= 1]
for k in cand:
    if k in self.done or k in self.active:
        continue
    ...
```

**Keyed on:** nothing dynamic - `tier`, `ph`, `_total_cost` are static tree
data (set once in `data.load()`, never reassigned anywhere in the engine:
checked `grep` for `["tier"] =`, `["ph"] =`, `["_total_cost"] =`) and
`_is_foreign_institution` is itself static per point 1. **Invalidated:**
never needed - this is provably the same set of nodes `self.order` would
ever pass the old per-year filter on, in the same relative order, so
skipping the rest changes nothing about which nodes get granted or when:
a node not in `cand` was always going to fail the same
tier/ph/cost/foreign test again next year too.

### 3. `core.step()`, section 4a2 (auto-train): a *local*, step-scoped memo for `market_supply`/`trade_available`

```python
_ms_memo, _ta_memo = {}, {}
def _market_supply(t):
    v = _ms_memo.get(t)
    if v is None:
        v = _ms_memo[t] = self.market_supply(t)
    return v
def _trade_avail(t):
    v = _ta_memo.get(t)
    if v is None:
        v = _ta_memo[t] = self.trade_available(t)
    return v
```
used in place of `self.market_supply(t)` / `self.trade_available(t)` for
the two loops in this block (`for k in self.active: ...` and `for k in
self.order: ...`), and `_gone` hoisted out of the `for k in self.order`
loop (it closed only over `self`, never over `k`, so redefining it on
every one of ~2,800 iterations was pure waste, independent of the memo).

**Keyed on:** `t` (trade name), for the duration of **one call to
`step()`**. **Invalidated:** by construction, not by tracking - `_ms_memo`
and `_ta_memo` are plain local variables created fresh every time `step()`
runs and discarded when the `if self.policy.get("auto_train", ...)` block
ends; nothing outside that block can read them, so there is no "stale"
state for them to have. This is safe specifically because:
- `self.employees` (which both functions read via `.get()`) is mutated
  earlier in `step()` (attrition, forced departures, `auto_hire` top-up -
  all before line ~680) and not again until a training row matures at the
  *start* of a **future** `step()` call; nothing in sections 4a/4a2 itself
  writes `self.employees`.
- `self.trades_created` (read by `trade_available`) is mutated by
  `train()`, which is called **once**, **after** both loops that use the
  memo, for at most one trade (`want.items())[:1]`) - so no memoized value
  is read again after it could have gone stale within this call.
- `running()` (read by `market_supply` for `school_founded`,
  `patron_imperial`, `academy_network`, `interchangeable_parts`) depends on
  `self.done`/`self.operating`/`self.granted`, none of which this block
  mutates either.

I checked this by reading every assignment to `self.employees[...]` across
`engine/*.py` (`core.py:341,342,399-404,450,452,475`; `labour.py:719-720`;
`society.py:589`) and confirming all of them happen either earlier in the
same `step()` or in code paths this block never calls.

## Safety proof

### Regression suite

```
$ python3 rome/sim/test_regressions.py             # fast set
562 checks, 0 failures, 156s
$ python3 rome/sim/test_regressions.py --slow      # includes the two
567 checks, 0 failures, 416s                        # determinism checks
```
Both runs are 0 failures, including:
- "the same seed gives the same run, twice in one process"
- "...and the same run in a process with a different string hash seed"
(the two checks the task brief specifically flagged as the ones that would
catch a determinism break from an unsorted-set or reordered float sum).

### Identical final state, 3 seeds x 2 civilizations, full 600-year run

Recorded before the change (reverted to the committed `HEAD` versions of
`core.py`/`society.py`) and after (with all three changes applied), using
`events=True, manual=False`, run to horizon or goal, via `s.run(GOAL)`:

| civ | seed | year | goal_year | len(done) | capital | scholars | artisans | sha256(sorted done)[:16] | identical? |
|---|---|---|---|---|---|---|---|---|---|
| rome_100ad | 1 | 600 | None | 351 | -4712.030157 | 0.025883 | 0.239973 | 72f467ac44651e43 | yes |
| rome_100ad | 2 | 600 | None | 262 | -5043.722352 | 0.139219 | 0.417181 | 79d2186b59cb968e | yes |
| rome_100ad | 3 | 600 | None | 329 | -12143.828034 | 0.140056 | 0.161923 | 0d0512648d520f0b | yes |
| han_china_100ad | 1 | 600 | None | 335 | -5790.518209 | 0.306033 | 1.215530 | 30e977a65a30bae9 | yes |
| han_china_100ad | 2 | 396 | 395 | 2825 | 758631651.894603 | 164.239187 | 403.190773 | 56c975b1b143655a | yes |
| han_china_100ad | 3 | 600 | None | 321 | -11075.669063 | 0.423783 | 1.738017 | 236a8d36f30d81b0 | yes |

`diff` of the before/after dumps (6 lines, every field above plus
`dead_reason`) is empty - byte-for-byte identical in every field, for every
seed, on both civilizations, including the one run (han seed 2) that
actually reaches the goal.

### Speedup

150 steps, `events=False, manual=False`, `cfg` defaults, min of 5 reps,
**CPU time** (`time.process_time()`, not wall clock - this sandbox is
shared with other concurrent jobs and wall-clock varied 2-3x run to run
under unrelated load; CPU time did not):

| civ | before (s) | after (s) | speedup |
|---|---|---|---|
| rome_100ad | 2.485 | 1.814 | 1.37x |
| han_china_100ad | 4.303 | 2.713 | 1.59x |

Call counts for the same 150-step rome_100ad profile run: **11,589,923 ->
8,566,904** total calls (26% fewer). The single biggest drops:
`_is_foreign_institution` 424,650 -> 2,831 (150x), `market_supply` 293,961
-> 17,949 (16x), `trade_available` 792,622 -> 21,619 (37x), `running()`
1,237,425 -> 133,377 (9x).

A Monte Carlo batch of dozens of full 500-700-year runs should see
something in this range or better: the fixes scale with tree size and
years simulated, both of which are unchanged between a 150-step sample and
a full run, and civilizations other than Rome benefit more (han_china's
call count dropped from 19.5M to 9.6M for the same 150 steps - just over
2x - because `_is_foreign_institution`'s string search, which is a no-op
for Rome, is real work there).

## Identified but NOT applied

- **Caching `start_reason`/`can_start` itself.** This is now the single
  largest remaining cost (221,487 calls, ~1.6-2.3s cumulative out of
  ~4.7-5.4s total). Its result depends on `self.done`, `self.active`,
  `self.capital`, `credit_frozen_until`, `insolvent_years`, scholar/artisan
  staff levels, substitution-material availability, and `state_interest`
  (reputation/protection) - none of which are gated behind a single
  "changed" flag the way `self.done` is behind `_done_changed()`. A cache
  keyed only on "did `done` change" would be *wrong* on any year where
  capital, staff or reputation moved without a new technology completing,
  which is most years. Auditing every dependency well enough to build a
  correct multi-key cache was more risk than the remaining win justifies
  under the "correctness over speed" instruction, so I left it alone.
- **The "4b start new projects" loop's `room`/`fixed` computation**
  (`core.py`, `for k in candidates: ... fixed = self.upkeep() +
  self.living_cost() + ...`). At first glance `revenue()`/`upkeep()` look
  invariant across the candidates loop (nothing in the loop body changes
  `done`/`operating`/`granted`), which would let them be hoisted out and
  computed once. But `living_cost()` reads `self.capital` directly (for
  the "appearances" term), and `post_bounty()` - called from inside this
  very loop - mutates `self.capital`. So `living_cost()`'s value can
  legitimately change mid-loop whenever a bounty is posted, and hoisting
  it out would be wrong on exactly those runs. Not applied.
- **`society.needs_first`** (219,262 calls, 0.183s cumulative): iterates
  the civ's `needs_first` spec entries linearly per call. A reverse index
  (`node_id -> (gate_node, reason)`) built once would turn this into a
  dict lookup, but the original loop's fallthrough behavior - if a node id
  matches one spec entry whose gate is already satisfied, it keeps
  checking *later* entries for the same id - is only safe to replace with
  "first match wins" if no civilization file ever lists the same node id
  in two different `needs_first` entries. I did not verify that across
  all five civilization files, so I left this alone rather than risk a
  behavior change for a 3%-of-total-time function.
- **`projects.running()`** is already minimal (two set-membership checks);
  its huge call count (1.24M before, 133K after) was a symptom of the
  `market_supply` problem, not a problem of its own, and is already fixed
  by change 3 above.

## Files touched

- `/home/user/test/rome/sim/engine/core.py` - changes 2 and 3.
- `/home/user/test/rome/sim/engine/society.py` - change 1.

No other files were modified. Nothing was committed.
