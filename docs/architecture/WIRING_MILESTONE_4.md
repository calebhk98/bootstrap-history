# Wiring Milestone 4: what breaks when demography and agriculture go in

**Status:** analysis, not a plan anyone has approved. Written against anchor
commit `798a027` (branch `claude/youthful-goldberg-9ay3su`) while four other
agents edited `sim/world/deposits.py`, `sim/solve_prices.py`,
`sim/prove_rename_safe.py` and `sim/engine/economy.py` concurrently in the
same checkout; every count below that touches those four files was taken by
reading `798a027`'s own copy of them (`git show 798a027:<path>`), not the
live working tree, so it cannot have been perturbed by that concurrent work.
`git diff --stat 798a027` at the time of writing showed exactly one file
diverged from the anchor, `sim/engine/economy.py` (+402/-34 lines); every
other file this document cites was identical to its anchor-commit copy.

This document does not change any code. It exists to answer one question
before anyone starts changing code: **what, specifically, breaks when
`sim/world/demography.py` and `sim/world/agriculture.py` are wired into
`sim/engine/`, and in what order can it be done so that each step is checked
before the next one is attempted.**

Nothing here should be read as "the design." Several places below are
decision points a plan would still have to make (marked **OPEN**); this
document's job is to make sure those decisions get made on purpose, with the
actual call sites in front of whoever makes them, rather than discovered one
test failure at a time.

---

## 1. The surface

### 1.1 What demography.py replaces

Everything below was found with:

```
grep -rn "\.pop_scale\b\|\.pop_deficit\b\|\.wage_index\b" sim/engine sim/engine/proto
```

against the anchor commit, cross-checked against `docs/architecture/
SIM_STATE_INVENTORY.md`'s own independently-derived table (built by an AST
walk, not a grep, so agreement between the two is a real cross-check, not
one number quoted twice).

Nine `Sim` instance attributes implement the mechanism (`sim/engine/core.py`
lines given are anchor-commit lines):

| Attribute | Set | Read/written from | Files (per SIM_STATE_INVENTORY) | Sites |
|---|---|---|---|---|
| `pop_scale` | `core.py:59` (`__init__`), `core.py:1267` (`_refresh_demographic_indexes`) | economy.py, labour.py, projects.py, geography.py, core.py | 5 | 19 |
| `pop_deficit` | `core.py:71`, `society.py:2239` (`_shocks`) | core.py, society.py | 2 | 9 |
| `wage_index` | `core.py:56`/`1279` | core.py, labour.py, economy.py, proto/dispatch.py, proto/economy.py | 6 | 16 |
| `_pop_scale_base` | `core.py:70`, `society.py:1450` (`_advance_food_diffusion_population`) | core.py, labour.py, society.py | 3 | 8 |
| `_pop_recovery_years` | `core.py:72`, `society.py:2240` | core.py, society.py | 2 | 5 |
| `_pop_tech_pending` | `core.py:79`, `society.py:773` (`apply_tech_effects`) | core.py, society.py | 2 | 5 |
| `_wage_index_base` | `core.py:57` | core.py | 1 | 3 |
| `_said_wage_cascade` | `core.py:244` | core.py | 1 | 3 |
| `_food_pop_bonus_applied` | `society.py:1450` (lazy) | society.py; **is a `SAVE_FIELDS` member already** | 1 | 3 |

That is **9 of Sim's 165 instance attributes** (measured count from
`SIM_STATE_INVENTORY.md` §0, itself AST-derived, not a re-estimate).

Two of these attributes are reached only from `sim/engine/proto/` (`s.X`,
never `self.X` inside the six mixins), which is exactly the class of
attribute `sim/ARCHITECTURE.md` warns is easy to miss:

```
sim/engine/proto/dispatch.py:1365:  "demographic_scarcity": round(s.wage_index, 3),
sim/engine/proto/dispatch.py:1411:  "wage_per_hour": round(WAGES[t] * s.wage_index ...
sim/engine/proto/economy.py:598:    "wage_index": round(s.wage_index, 4),
sim/engine/proto/economy.py:648:    "wage_index": round(s.wage_index, 4),
sim/engine/proto/economy.py:682:    "demographic_scarcity": round(s.wage_index, 3),
```

Neither `pop_scale` nor `pop_deficit` is read from `proto/` directly — only
their derived `wage_index` crosses into the JSON protocol layer. That
matters for Part 6: the protocol-facing surface of this mechanism is one
attribute, not three.

**The two functions in `labour.py` that reconstruct an absolute headcount
from the scalar model** are the real prize for this wiring, and are easy to
miss because neither has "demograph" or "pop_scale" in its own name:

```python
# sim/engine/labour.py:1286 (anchor commit), inside national_trade_population
reference_pop = float(self.civ.get("population", 0.0))
scale_from_baseline = (self.pop_scale / self._pop_scale_base
                       if self._pop_scale_base else 1.0)
pop = reference_pop * scale_from_baseline
```

The identical three lines are repeated at `labour.py:1336` inside
`population_report()`, which is what backs the `population` JSON command
(`proto/dispatch.py:1343: return {"ok": True, **s.population_report()}`).
This is the ONE place in the engine that currently tries to answer "how many
people are actually here" as a headcount rather than a ratio, and it is
built entirely out of `civ["population"]` (a fixed config number, e.g.
`data/civilizations/rome_100ad.json`'s `"population": 65000000`) times a
ratio of two scalar fields. `demography.Population.total` and
`.working_age_population` are direct, better-typed replacements for exactly
this computation, and `national_trade_population`'s per-trade pools
(scholar via `literacy_elite`, scribe via `literacy_general`, everything
else via `TRADE_DENSITY`) are downstream consumers worth wiring at the same
time, not separately, since they exist only to serve this one function.

**`65e6` (Rome's own configured population) is baked in as the universal
cross-civilisation reference**, not just Rome's own baseline:
`pop_scale = civ["population"] / 65e6` at construction. Every downstream
formula that reads `pop_scale` (hiring caps, mineral-market access, the
capital ceiling, the credit-line `tau`) was calibrated assuming
`pop_scale == 1.0` means "a Rome-sized labour market." If `pop_scale`
becomes a computed property off `self.population.total`, it should stay
`self.population.total / 65e6` — the SAME constant — precisely so those ~19
call sites do not all need to be re-derived in this milestone. See §6.

### 1.2 The adjacent (not identical) surface: `farm_hectares`

`agriculture.py` does not replace an engine mechanism the way `demography.py`
replaces `_demographic_recovery`, because the engine currently has no
civilisation-wide food supply at all. What it DOES have is a household-scale
investment heuristic, unrelated in shape:

```python
# sim/engine/economy.py:1354-1388 (anchor commit)
def essential_price_ratio(self):
    ...
    farm_ha = max(0.0, getattr(self.household, "farm_hectares", 0.0))
    farm_ratio = max(0.55, 1.0 / (1.0 + farm_ha / 120.0))
    return min(market_ratio, farm_ratio)

FARM_COST_PER_HA = 75.0
def invest_farm(self, hectares):
    """Buy productive farmland that lowers the household staple price."""
```

This is a founder-owned purchase (`farm_hectares` lives on `Household`, is a
`SAVE_FIELDS` member) that cheapens the FOUNDER's own cost of living through
an authored `1/(1+ha/120)` curve with a `0.55` floor — no land quality, no
labour, no weather, no population anywhere in it. `agriculture.py`'s
`Land`/`Storage`/`Cobb-Douglas` model has no household-ownership concept at
all; it answers a civilisation-scale question (`Storage.step` takes a
`population` headcount and land in hectares, nothing about who owns either).
Wiring agriculture.py does not delete `invest_farm`/`essential_price_ratio` —
they answer a different question (does the founder's own farm cheapen the
founder's own bread) that a civ-wide grain model does not automatically
supersede. Whether they should eventually be re-expressed as one household's
draw on the same shared `Land`/`Storage` (so a founder's farm is a claim on
the same national wheat market rather than a private multiplier) is a real
question but **outside this milestone**; flagged, not solved.

### 1.3 The three write sites, and why they matter more than the read sites

Read sites (§1.1's ~19+16+9 count) are formulas that consume a number.
**Write sites are the ones that have to be redesigned, not just repointed**,
because each one currently mutates state the new model does not have:

1. `society.py:2239` (`_shocks`, inside the `staff_loss` hazard branch —
   the ONE branch every plague, famine and epidemic hazard in every
   civilisation file funnels through; see §2).
2. `society.py:773` (`apply_tech_effects`, the `elif field == "population":`
   branch — 14 technologies in `data/civilizations/_TECH_EFFECTS.json`
   declare a `"population"` delta, queued into `_pop_tech_pending` and
   drained by `_demographic_recovery`).
3. `society.py:1441-1450` (`_advance_food_diffusion_population` — food-
   category technology diffusion raises `_pop_scale_base` directly, capped
   at `FOOD_DIFFUSION_POP_BONUS_MAX = 0.25`, tracked by
   `_food_pop_bonus_applied`).

All three are read-modify-write against exactly the state
`_demographic_recovery`/`_refresh_demographic_indexes` manage together, and
all three currently bypass the tree entirely — they add a fraction to a
scalar. Each is a design decision for §6, not a mechanical repoint:
(1) is "how does a hazard cut a cohort-structured population instead of a
scalar", (2) and (3) are "how does a technology raise `Population`'s
capacity instead of nudging a baseline" — and (2)/(3) both currently read
module-level constants in `demography.py`
(`BASELINE_ANNUAL_MORTALITY_RATE_*`) that have no per-instance override, so
"this civilisation's population now has lower mortality because it has
antisepsis" has nowhere to live yet. **OPEN.**

---

## 2. What gets deleted, and what reads it

`_demographic_recovery` (`core.py:1220`) and the deficit-decay half of
`_refresh_demographic_indexes` (`core.py:1252`) are the obvious deletions.
Measured, not assumed, by grepping every non-`sim/world` occurrence of the
name:

```
sim/tests/test_round10.py:478,493,496,530,538   (calls _demographic_recovery directly)
sim/tests/test_demography.py:239,307             (describes it in prose, as the thing being falsified)
```

`test_round10.py` calls `_demographic_recovery` directly five times, against
constructed `Sim` objects, to assert:

- `s.pop_deficit == 0.45` immediately after a staff_loss shock is applied by
  hand (line 456) and again after a second identical shock compounds onto
  the first (line 469, `1 - (1-0.45)*(1-0.45)` compounding, not `0.45+0.45`);
- `s.wage_index > _normal_wage * 1.2` while the deficit is open (line 480);
- `s4._demographic_recovery` called twice n years apart shows the wage
  premium decaying (`_mid_premium`, `_end_premium`, lines 494/497);
- `s6._pop_scale_base` increases by queued technology deltas exactly once
  per pending year and then stops (lines 524-542).

Every one of these assertions is about the SHAPE `test_demography.py`
explicitly falsifies (a size-only deficit with a size-only clock). They
cannot be "fixed" to pass against the new model; they have to be deleted or
rewritten to assert on cohort composition instead — rewriting them is itself
evidence the milestone is progressing, not an unfortunate side effect.

`test_complaints_17_24.py:7-14` constructs a `Sim`, sets `.pop_deficit = 0.28`
directly, and asserts `wage_index > _wage_index_base`. This one is a soft
dependency: it never calls `_demographic_recovery`, only
`_refresh_demographic_indexes` indirectly (via whatever reads `wage_index`
next), so it breaks only if `pop_deficit` stops existing as a settable
attribute — worth deciding whether to keep `pop_deficit` as a **derived,
read-only** property for exactly this kind of external setter to fail loudly
on, versus deleting the name outright.

`test_craftsmen_wording.py` and `test_demographics.py` read `pop_scale` and
`_pop_scale_base` (12 combined hits) to construct expected hiring-cap and
wage-bill numbers by hand; these need the same treatment as `test_round10.py`
but are checking DOWNSTREAM formulas (hiring caps, wage bills) that can be
kept correct as long as `pop_scale` keeps returning a number of the same
shape — see §6's argument for keeping `pop_scale` as a computed property
specifically so these do not also need rewriting in the same commit.

**A larger, softer deletion candidate, sized but not attempted here:** the
milestone-4 acceptance line in `ENDOGENOUS_COSTS_AND_DOMAINS.md` reads "a
food shortage raises mortality and wages through the ordinary machinery,
**with no famine modifier anywhere**." Taken literally, that means the
`staff_loss`-only hazard entries in the civilisation files — the ones with
no `sack_chance`/`output_factor` alongside them, i.e. disease and famine,
never war (see `society.py`'s own comment at the `_military_war_relief`
docstring for that exact distinction) — are themselves the modifiers the
milestone is meant to make unnecessary. Measured:

```
$ python3 -c "... count staff_loss entries with no output_factor across data/civilizations/*.json ..."
12 of 74 total hazards, across 4 of 5 civilisation files (all but han_china_100ad,
whose staff_loss entries are all rebellions and carry output_factor too):
  england_1300: Great Famine, Black Death, dearth of the 1590s,
                Great Plague of London, great frost/dearth of 1740  (5)
  mexica_1500:  Old World epidemics on contact, matlazahuatl of 1736 (2)
  norse_900ad:  Black Death in Scandinavia                          (1)
  rome_100ad:   Antonine plague, Plague of Cyprian,
                Justinianic plague, Recurrent plague                (4)
```

I would NOT delete these in this milestone — see §7 — but a plan that claims
Milestone 4's acceptance bar is met without touching them is claiming
something the plan document's own words do not support.

---

## 3. `SAVE_FIELDS`

**None of the nine attributes in §1.1 are in `SAVE_FIELDS` today.** Verified
by AST-parsing the tuple (`sim/engine/proto/saveload.py`, 98 distinct field
names across 99 string literals — matches `SIM_STATE_INVENTORY.md`'s own
count) and grepping it for every name in §1.1: zero hits. This is not a
hypothesis; it was checked twice, by two different methods.

**This is a live, currently-shipping bug, not a hypothetical risk of the
wiring, and it needs to be in the document because the wiring must not
reproduce it.** `--session` play constructs a brand-new `Sim` from the
civilisation file on every invocation and then calls `load_state` to
overwrite it with the save (`sim/engine/cli.py:912-921` for `play`,
`:1580-1586` for `agent`) — CLAUDE.md §5's "every single command is a save
followed by a load" is describing exactly this reconstruct-then-restore
sequence, and it is how `sim/tests/test_early_playtest.py`'s own save-reload
regression test drives the game (two separate `subprocess.run` calls to
`agent --session`, each a fresh process). Reproduced directly:

```
$ python3 - <<'EOF'
# construct s1, set s1.pop_deficit = 0.45, call s1._demographic_recovery(year)
# -> pop_deficit=0.333, wage_index=1.300, pop_scale=0.667
# save_state(s1, path)
# construct a FRESH s2 the same way cli.py does on the next invocation
# load_state(s2, path)
EOF
before: 0.0 1.0 1.0 1.0
after shock applied: 0.333368199306773 1.3000313793760958 0.666631800693227
fresh s2 before load: 0.0 1.0
s2 after load_state: 0.0 1.0 1.0 1.0
```

A demographic shock's wage premium and population deficit are silently wiped
back to baseline the moment a `--session` game is resumed in a fresh
process, because the fields that would carry it are not on the list of
things a save restores. Every downstream number that depends on `pop_scale`/
`wage_index` (hiring caps, mineral access, credit-line tau, the capital
ceiling) is correspondingly wrong for one command and then self-heals, which
is a second, quieter symptom of the same gap. **This is exactly the
`perf_fingerprint.py`-catches-what-tests-miss situation `sim/ARCHITECTURE.md`
§6 warns about, except no regression test caught it because none of
`test_round10.py`/`test_complaints_17_24.py`/`test_demography.py`/
`test_demographics.py` drives a hazard through an actual save/reload cycle —
they all construct one `Sim` and call `_demographic_recovery` directly in
the same process.**

Per CLAUDE.md §3.5, fixing this is not a migration question — there is
nothing to migrate, because no save ever correctly round-tripped this state
to begin with. It is simply a field that needs to exist.

**What the wiring must add, concretely:** the three cohort counts
(`children`, `working_age`, `elderly` — plain floats, `demography.Population`
already stores them this way) need three new `SAVE_FIELDS` entries (or one
struct-shaped entry; the existing tuple has no precedent for a nested
object, so three flat floats, matching how `mine_tranches` etc. store
structured-but-flat data, is the smaller change). **Open, and worth deciding
explicitly rather than by default:** `Population` owns a `random.Random`
instance for the `jitter=True` path (never used by `stationary()`, and — per
§6 — should not be turned on inside the engine's own `step()` call either,
at least not in this milestone), so as long as the engine never passes
`jitter=True`, that generator's state never advances and does not need its
own save slot. If a later milestone turns jitter on, it needs the same
special-cased treatment `self.rng` already gets (`blob["_rng"] = ...`,
outside `SAVE_FIELDS` entirely, because a `random.Random` is not
JSON-serialisable) — flagged now so nobody re-discovers it as this
milestone's own surprise.

**What disappears from `SAVE_FIELDS`:** nothing — none of the nine
attributes in §1.1 were ever there, so there is no drop, only an addition,
which is a smaller and safer change than the "rename or drop freely, no
migration" framing in CLAUDE.md §3.5 might suggest to expect. The genuine
§3.5-flavoured decision is `_food_pop_bonus_applied`, which IS in
`SAVE_FIELDS` today and tracks a mechanism (§1.3 item 3) that this wiring
should retire or redesign; dropping that one field is the only true "drop a
persisted field" case this milestone raises, and per §3.5 it needs nothing
more than removing the string from the tuple.

**Units, not just presence:** no field in `SAVE_FIELDS` changes units as a
result of this wiring — `pop_scale`/`wage_index` stay dimensionless ratios
if kept as computed properties (§6), and the new cohort fields are a
headcount (people), the same unit `civ["population"]` already uses. The
place a unit actually changes is not in the save file; it is at the
agriculture/demography boundary itself — see §4.

---

## 4. The unit mismatches

Three distinct crossings, not one. Confusing them with each other is exactly
how a wiring job goes wrong silently rather than loudly.

### 4.1 FTE workers vs. people (the one agriculture.py's own docstring names)

`fraction_of_population_that_must_farm()` (`sim/world/agriculture.py:1812`)
computes a share of **full-time-equivalent farm WORKERS**:

```python
output_per_worker_kg = hectares_cropped_per_farm_worker(crop, toolkit) * food_available_per_ha_kg
return annual_food_demand_kg_per_person(crop) / output_per_worker_kg
```

`hectares_cropped_per_farm_worker` is denominated in
`ANNUAL_LABOUR_HOURS_PER_FARM_WORKER` (1,400 hours/worker/year — a
`temporary_heuristic`, no source, `agriculture.py:322`) — i.e. this is a
share of the population's LABOUR-HOUR CAPACITY that must go to farming, not
a share of PEOPLE. The historical 80-90% target
(`HISTORICAL_FARM_POPULATION_SHARE_LOW/HIGH`) counts every person LIVING IN
a farming household — children, the elderly, the household's own spinners
and tool-menders — not full-time field-workers. Converting one to the other
needs a dependency ratio: (people per working-age adult), which is exactly
`demography.Population.total / demography.Population.working_age_population`
once the two are wired together — a quantity `agriculture.py` explicitly
does not have on its own (its own docstring, reason (a) under "ON THE
HEADLINE NUMBER", names this precisely) and `demography.py` can supply
directly, with no new mechanism, once wired.

### 4.2 The engine's OWN hours-per-worker-year figure disagrees with agriculture.py's

Independent of the FTE-vs-people gap above, the two sides of this wiring do
not even agree on how many hours one worker-year is:

```python
# sim/engine/economy.py:4513 (anchor commit)
HOURS_PER_PERSON_YEAR = 2000.0   # prices.json: a 10-hour day, 250 days, less feasts
```
```python
# sim/world/agriculture.py:322-323
ANNUAL_LABOUR_HOURS_PER_FARM_WORKER = declare(
    "ANNUAL_LABOUR_HOURS_PER_FARM_WORKER", 1400.0,
    ..., unit="hours/worker/year", ...
    why="...Pre-industrial farm labour is famously seasonal...")
```

A 30% gap (2000 vs. 1400), and it is not a bug in either number — the engine's
figure is a generic hired-labour year, agriculture.py's is specifically
seasonal field labour, and the two are declared for different reasons. But
anyone converting a `labour_hours` pool between the engine's labour market
and `agriculture.Storage.step` (which takes an aggregate `labour_hours`
pool, in hours, matching the tree's own `lab` field convention — see
`ENDOGENOUS_COSTS_AND_DOMAINS.md` §2.1: "`hours_per_unit` is [the tree's]
`lab` field, in hours by trade") has to pick ONE of these two figures
explicitly and say why, rather than silently using whichever constant
happened to be in scope at the call site. **OPEN, and worth a `declare()`d
constant of its own rather than a silent choice between the two existing
ones.**

### 4.3 Adult-equivalent calories vs. flat per-head calories, on the SAME loop

This one is not named in either module's own docstring, because it only
appears once the two modules are actually connected — it is exactly the
kind of thing this document exists to surface before that happens.

`Storage.step` (`agriculture.py:1699`) computes demand as:

```python
food_demand_kg = population * annual_food_demand_kg_per_person(crop)
```

— a flat per-HEAD calorie requirement (`HUMAN_ENERGY_REQUIREMENT_KCAL_PER_
ADULT_DAY = 2200.0`, applied uniformly to every person regardless of age).

`Population.nutrition_ratio` (`demography.py:539`) computes the denominator
of the number that then judges whether that harvest was enough as:

```python
adult_equivalent_population = (self.children * CHILD_CALORIE_EQUIVALENT     # 0.5
                              + self.working_age * 1.0
                              + self.elderly * ELDERLY_CALORIE_EQUIVALENT)  # 0.85
ratio = food_available_calories_per_day / (adult_equivalent_population * SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY)
```

Both modules independently declare the SAME 2,200 kcal/adult/day figure
under different names (`demography.py`'s own docstring for
`SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY` says so explicitly: "the
same figure ... a future agriculture module might declare under a similar
name, deliberately [not imported], since this module has no dependency on
[it] and should not silently start requiring one just because a name
happens to collide") — so the constant itself is not the problem. The
problem is that if `population` in `Storage.step` is fed
`demography_population.total` (a plain headcount, which is the natural
thing to pass, since `Storage.step`'s signature wants a number of people),
the DEMAND side asks for enough calories to feed every child and every
elderly person a FULL adult ration, while the SUPPLY side (once that same
harvest is fed back into `nutrition_ratio`) is judged against a SMALLER
adult-equivalent-weighted population. Concretely, for a population that is
demography's own stationary age structure (roughly 35-38% children given
`SURVIVAL_TO_WORKING_AGE = 0.50` over a 15-year child band; elderly a
smaller share again), the adult-equivalent population is on the order of
10-15% below the flat headcount — so a harvest computed to exactly meet
`Storage.step`'s own demand would show `nutrition_ratio` PERSISTENTLY ABOVE
1.0 by roughly that same 10-15%, forever, with no shock anywhere, purely
from feeding the same population number into two functions that weight ages
differently. Whether that shows up as "harvests are quietly too generous"
or "population grows for no modelled reason" depends on which of the two
functions actually reads which variable once they're wired — either way, it
is not a shock and it is not a bug in either module in isolation; it is a
wiring-time unit mismatch that needs one of: (a) `Storage.step` taking an
adult-equivalent count instead of a headcount (which needs `demography.py`
to expose that quantity — it currently computes it inline inside
`nutrition_ratio` and does not return it), or (b) accepting the ~10-15% gap
explicitly as a known, labelled simplification. **OPEN.**

---

## 5. What the fingerprint will do

`sim/perf_fingerprint.py`'s `FIELDS` is `SAVE_FIELDS` minus `"log"` — it
compares exactly, and only, the tuple examined in §3. Two consequences
follow directly from §3's finding that none of the nine mechanism attributes
are in that tuple today, and both are worth stating before anyone runs
`check` and has to explain the result after the fact:

**Before any cohort field is added to `SAVE_FIELDS`, the fingerprint cannot
see this mechanism change AT ALL**, even though `pop_scale`/`wage_index`
feed vast swaths of `economy.py`/`labour.py`/`projects.py`. It can only see
the mechanism's DOWNSTREAM footprint — `economy`, `capital`, `employees`,
`wages_paid`, `mines`, `hour_allocations` and everything else in
`SAVE_FIELDS` that a `pop_scale`-driven formula eventually feeds. This is
not a gap in the tool; it is exactly why §3's commit ordering puts "add the
cohort fields to `SAVE_FIELDS`" as its own, separately-checked step (§6) —
once they're there, `perf_fingerprint` starts hashing the actual state that
matters, not just its shadow.

**Once the mechanism is swapped, divergence should appear at year INDEX 0,
on all nine scenarios, and this is the correct result, not a sign of a
bug.** The reasoning, stated so it can be checked against what actually
happens rather than rationalised afterwards:

- The OLD model is exactly stationary absent a hazard or a completing
  technology: `_demographic_recovery` only touches `pop_deficit` if it is
  `> 1e-6`, and does nothing at all if `_pop_tech_pending` is empty. A
  scenario with no hazard yet and no relevant technology finished leaves
  `pop_scale` at EXACTLY the same float, bit for bit, year over year,
  forever.
- The NEW model cannot do that even in principle, by construction:
  `Population.step()` computes births and deaths from the cohort counts
  EVERY year, and demography.py's own docstring says the model is not
  perfectly self-replicating even at exact subsistence ("net drift over 300
  years at subsistence under -0.1%" — i.e., genuinely non-zero, just small).
  So `population.total` moves by a small amount every single year, with no
  shock required.
- Separately and more basically: `Population.stationary()`'s own
  construction (`scale = total_population / probe.total`, then rescaling
  three separate floats and re-summing them) cannot be guaranteed to
  reproduce `total_population` to the last bit of a `repr()`-compared float
  — `perf_fingerprint`'s `_canon()` uses `repr()`, not `round()`, precisely
  so a last-bit change counts as a real difference (see `_canon`'s own
  comment: "a change that alters the last bit of a float IS a change, and
  this harness exists to catch exactly that"). So even the STARTING value
  of a `pop_scale`-shaped quantity under the new model is extremely unlikely
  to be bit-identical to the old model's exact `civ["population"] / 65e6`.

Putting those together: **all nine scenarios are predicted to diverge, and
to diverge starting at year index 0** — before the Antonine plague, before
the Black Death, before any hazard fires at all — because the population
figure itself is now a different KIND of number (one with built-in
numerical drift) from year zero, not because anything dramatic has to
happen first.

**What would then distinguish "correct, expected divergence" from "the
wiring is wrong":**

- The events=False control, `rome_100ad/seed3` (the only one of the nine
  scenarios with `events=False`, so `_shocks()` never runs and no random
  hazard can contaminate the comparison) should show ONLY this small,
  smoothly-growing drift — no jumps. If it instead shows a large,
  discontinuous jump at some year, or diverges only in fields unrelated to
  population/wages/economy (e.g. a materials ledger, or an RNG-dependent
  field like a random event's own text), that means something is consuming
  `self.rng` draws it should not be (shifting every subsequent random
  choice, the same class of accidental side effect `Complaints/27`
  describes for a different cache), because `demography.Population` is
  built to use its OWN, separate `random.Random` and never touch the
  engine's shared generator — a genuine violation of that boundary is
  exactly the kind of thing this prediction is designed to catch.
- The events=True scenarios should each show a SECOND, sharply larger jump
  in divergence magnitude at the year (or within the window) their own
  civilisation's first population-relevant hazard fires — measured directly
  from each civ's own hazard table (`data/civilizations/*.json`), not
  guessed:

  | Scenario | Horizon | First staff_loss hazard inside horizon | Expected extra jump |
  |---|---|---|---|
  | rome_100ad/seed1, 200y (100-300 AD) | ends 300 | Antonine plague, 165-180 (staff_loss 0.28) | ~year 65-80 |
  | rome_100ad/seed2, 200y+fog | ends 300 | same window (RNG differs, so exact fire year may shift within it) | ~year 65-80 |
  | rome_100ad/seed3, 200y, events=False | ends 300 | **none — control, see above** | none |
  | han_china_100ad/seed1, 200y (100-300 AD) | ends 300 | none (first is 307-317) | **none — second control** |
  | han_china_100ad/seed2, 200y+fog | ends 300 | none | none |
  | norse_900ad/seed1, 200y (900-1100 AD) | ends 1100 | none (Black Death is 1349-1351) | **none — third control** |
  | england_1300/seed1, 200y (1300-1500) | ends 1500 | Great Famine 1315-1317 (0.12), then Black Death 1348-1350 (0.45) | ~year 15-17, then a much larger one ~year 48-50 |
  | mexica_1500/seed1, 200y (1500-1700) | ends 1700 | Old World epidemics 1520-1600 (staff_loss **0.8**, the largest in the whole tree) | ~year 20, the single largest jump of all nine scenarios |
  | rome_100ad/seed7, 400y (100-500 AD) | ends 500 | Antonine (165), Cyprian (249), crossings/sack of Rome (406-460) | three successive jumps |

  Three of the nine scenarios (both `han_china_100ad` runs and
  `norse_900ad/seed1`) have NO population-wide hazard inside their horizon
  at all, purely as an artefact of how long each one runs — that was not
  designed into `perf_fingerprint.py`'s scenario list for this purpose, but
  it means those three are, by accident, additional controls: any large,
  sudden divergence in them would need a different explanation than "a
  plague fired", because none does.

- If a hazard year comes and goes with NO visible change in the divergence
  trend, that specifically means `_shocks()`'s rewritten `staff_loss` branch
  (§1.3 item 1) was not actually connected to the new `Population` object —
  the mechanism swap happened but the hazard wiring did not, which
  `perf_fingerprint` alone cannot distinguish from "nothing happened" without
  this table to compare against.

None of this can be checked without the new code existing; it is written
down now, before that code exists, specifically so the check is a
prediction being confirmed or falsified rather than a result being narrated
afterwards.

---

## 6. The order

Each step is independently verifiable and, until the step marked below,
provably inert — every step before it must show ZERO fingerprint
divergence, because nothing has been read yet.

**Step 0 (not a commit).** `python3 sim/perf_fingerprint.py record
milestone4_start.json` at the true starting point, kept outside the repo
(these baseline files are working artefacts, not committed data). Every
`check` below is against this one file until Step 3 explicitly re-baselines.

**Commit 1 — make the modules reachable, read by nothing.**
`sim/simulator.py` (and the equivalent guarded inserts in
`sim/engine/cli.py`) currently put ONLY `sim/` itself on `sys.path`
(`sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`), which is
why running `sim/world/agriculture.py` directly fails outright
(`ModuleNotFoundError: No module named 'sim'` — reproduced directly). Add a
second, repo-root insert, the same pattern `sim/test_regressions.py` already
uses for `_ROOT`. This is required, not optional, because
`sim/world/demography.py` and `agriculture.py` import `sim.constants`
(fully-qualified) internally, and that never resolves under the engine's
existing `sim/`-only path. Verified empirically (both failure and fix): a
NAIVE relative import (`from ..world import demography`) inside
`sim/engine/core.py` fails with `ImportError: attempted relative import
beyond top-level package`, because `core.py` is loaded as top-level module
`engine.core`, not `sim.engine.core` — `engine` has no parent package under
`simulator.py`'s existing scheme, so `..` has nowhere to go. The working
form, confirmed against the real repo with both paths on `sys.path`, is a
BARE absolute import, `from world import demography` — matching the
engine's own existing style (`from constants import declare`, not
`from ..constants import declare`), and confirmed not to disturb
`sim/constants.py`'s own already-solved double-import hazard (its registry
is stashed under a fixed key in `sys.modules` for exactly this "imported
under two different dotted names" situation — see `sim/constants.py`'s own
comment on `_REGISTRY_HOME_KEY`, written anticipating this).
Construct `self.population = demography.Population.stationary(civ_pop)` in
`Sim.__init__`, seeded from something that does NOT draw from `self.rng`
(e.g. a fixed seed, or one derived from the civ id) — Population owns its
own generator and should not perturb the shared one this early, and this is
what makes this commit provably inert. Do not read `self.population`
anywhere else. Do not touch `SAVE_FIELDS`.
**Check:** `python3 sim/perf_fingerprint.py check milestone4_start.json` →
0 of 9 diverge, byte-identical. `python3 sim/test_regressions.py` → same
pass/fail counts as before the commit (module import alone changes
nothing). This is the LAST commit in the sequence required to pass that
check with zero divergence.

**Commit 2 — give the cohort counts a place in `SAVE_FIELDS`, prove the
round trip, re-baseline.**
Add the three cohort floats to `SAVE_FIELDS` (§3). Write the one regression
test this milestone most needs and none of the four `pop_deficit`-touching
tests currently provide: construct a `Sim`, run some years, apply a
hazard-shaped mutation to the cohorts directly, `save_state`, construct a
**fresh** `Sim` the way `cli.py` really does on the next `--session`
invocation, `load_state`, assert the cohorts come back bit-identical. This
is the exact failure mode §3 demonstrated for the OLD mechanism; the new one
must not repeat it. Decide and document (§3's open item) whether
`Population`'s own RNG needs a save slot — recommendation: not yet, as long
as the engine never passes `jitter=True`.
**Check:** the new round-trip test, run standalone. Then
`python3 sim/perf_fingerprint.py record milestone4_after_savefields.json` —
this is expected to differ from `milestone4_start.json` for a trivial reason
(the state DICTIONARY now has three more keys, always present with a
constant value, since nothing writes them yet) rather than a behavioural
one; that difference is not a bug and should not be chased as one. From
here on, `milestone4_after_savefields.json` is the reference.

**Commit 3 — the first commit allowed, and required, to change behaviour.**
Delete `_demographic_recovery`'s deficit-decay math, `pop_deficit`,
`_pop_scale_base`'s deficit role, `_pop_recovery_years`. Rewrite
`_shocks()`'s `staff_loss` branch (§1.3 item 1) to cut `self.population`'s
cohorts instead of accumulating a deficit — the design decision this needs
(age-differentiated cut using `STARVATION_VULNERABILITY_*`, vs. routing the
hazard through a temporary cut to `food_available_calories_per_day` and
letting `nutrition_ratio` do the differentiation on its own, which is more
in keeping with demography.py's own "no `famine_severity` switch" rule) is
named in §1.3 and left open here on purpose. Turn `pop_scale` and
`wage_index` into properties computed off `self.population` (keeping the
`/ 65e6` reference constant, per §1.1, so the ~19+16 downstream read sites
in economy/labour/projects/geography do not need to change in this commit).
Retire or rewrite the five `test_round10.py` assertions and the
`test_complaints_17_24.py` one that assert on the deleted names (§2).
**Check:** `python3 sim/perf_fingerprint.py check
milestone4_after_savefields.json` → **required** to show 9 of 9 diverging at
year index 0, matching §5's prediction table; a run that shows FEWER than 9
diverging, or divergence starting later than year 0 on any scenario, means
some read site still reaches the old computation. Re-run
`sim/tests/test_demography.py` and `sim/tests/test_agriculture.py`
unmodified (still standalone, still green — this commit does not touch
`sim/world/`) as a check that the wiring commit did not accidentally start
importing something that changes those modules' own behaviour.

**Commit 4 — rewire the two remaining write sites.**
`apply_tech_effects()`'s `"population"` branch and
`_advance_food_diffusion_population()` (§1.3 items 2-3) need a home now that
`_pop_scale_base` is gone. This is the commit where the **OPEN** item from
§1.3 has to be resolved: whether a population-raising technology becomes a
per-instance override of `Population`'s mortality/fertility parameters
(needs a new mechanism `demography.py` does not have — its constants are
module-level, not per-instance) or something else. Whatever is chosen,
`_food_pop_bonus_applied` (§3) is either retired or redefined against the
new mechanism, and that is the one genuine `SAVE_FIELDS` drop this milestone
makes.
**Check:** a fresh fingerprint baseline (this commit changes behaviour on
purpose, same as Commit 3) plus a targeted regression: run a scenario far
enough for a population-raising technology to complete and confirm the
population actually rises afterward, the same property `test_round10.py`'s
now-deleted `s6._pop_scale_base` check used to cover.

**Commit 5 — re-measure.**
Re-run whatever produced `sim/ARCHITECTURE.md`'s 165/411 counts and
`SIM_STATE_INVENTORY.md`'s table, and correct both: `pop_deficit`,
`_pop_scale_base`, `_pop_recovery_years` are gone; `population` (or
`pop_children`/`pop_working_age`/`pop_elderly`) is new; `pop_scale`/
`wage_index` move from stored attributes to computed properties, which
changes which column of `SIM_STATE_INVENTORY.md`'s table they belong in.
This is CLAUDE.md §8's own working rule, applied to this milestone rather
than deferred.

**Agriculture wiring is a parallel track, not a later step of this same
sequence**, because — per §1.2 — nothing existing needs to be deleted for
it, only added: introduce a shared `sim.Land`/`sim.Storage` (civ-scale, not
founder-owned), decide the §4.1/§4.2/§4.3 unit questions explicitly, and
feed `Storage.step`'s `food_available_kcal_per_day` into
`Population.step`'s `food_available_calories_per_day` — the one interface
`sim/world/__init__.py` already documents as the intended seam
("`Storage.step` below hands back exactly that number ... for the day
someone wires the two together"). It can start any time after Commit 1
(agriculture.py needs the same `sys.path` fix) and does not need to wait for
Commits 3-5.

---

## 7. What I would not do

**I would not decompose `Sim`.** `sim/ARCHITECTURE.md` already considered
and rejected a full decomposition — 157(→165) shared fields needing explicit
owners, ~200 implicit `self.x` couplings becoming arguments, most of 30,000
lines rewritten, against a small payoff, with `perf_fingerprint.py` not
covering `protocol.py` (a third of the code) at all. Nothing in this
milestone needs that. The smallest structural change that actually does the
job is **one new instance attribute** (`self.population`, a
`demography.Population`) plus turning two existing attributes
(`pop_scale`, `wage_index`) from stored values into computed properties —
the same shape `Household`'s own extraction already used successfully (104
forwarding properties over 68 attributes, per `sim/ARCHITECTURE.md`'s
"runtime graph" section), and precedented for exactly this reason: it lets
~35 downstream call sites keep reading `self.pop_scale` unchanged while
what backs it changes underneath them, without either rewriting all 35 in
one commit or reopening the decomposition question.

**I would not put `Population` on `Household`.** `Household` is
FOUNDER-scoped (money, staff, knowledge, standing); population is
CIVILISATION-scoped (the whole society's cohorts, read by many actors'
labour supply, not one household's). Milestone 3's own `HOUSEHOLD_
EXTRACTION.md` reasoning — "what stayed [on Sim] is the world, the scenario"
— already draws exactly this line; `self.population` belongs with `self.civ`
and `self.nodes`, not with `self.household`.

**I would not retire the civilisation files' famine/plague hazard entries
in this milestone**, even though §2 shows the plan document's own acceptance
line implies it eventually. Doing so before agriculture+demography's
combined trajectory has been checked against ANY historical range (§3.2's
own validation standard — distributions, not dated events) would replace
twelve authored numbers with a completely unvalidated model and call it
progress; CLAUDE.md §3.2 explicitly allows the baseline to get worse while
building toward this, but "worse and unmeasured" is not the same permission
as "worse and known to be worse." That comparison is Milestone 4's own
acceptance work, once the wiring in §6 exists to produce a trajectory to
compare.

**I would not try to close the §4.1 FTE-vs-people gap, the §4.2
hours-per-year disagreement, or the §4.3 adult-equivalent mismatch inside
this document or inside Commit 1-5's mechanical wiring.** Each is a real
modelling decision (which of two declared constants wins; whether
`Storage.step` needs a new parameter) that deserves its own reasoning and
its own test, not a default picked to make the wiring commit smaller. They
are named and left **OPEN** on purpose, per the task's own instruction that
a plan admitting what it could not establish is worth more than one that
guesses confidently and is wrong.

**I would not turn `jitter=True` on inside the engine's own `step()` call**,
even though `Population.step` supports it. `demography.py`'s own docstring
gives the reason: unconditional noise biases the long-run population down
for a reason that has nothing to do with real harvest variability and
everything to do with the model not yet having grain storage to damp it —
except the engine, once agriculture.py is wired (§6's parallel track), DOES
have grain storage (`Storage.stock_kg`). Turning jitter on is a Milestone-4
decision but a LATER one, after the storage-damping path is proven, not a
default to flip the day `Population.step` is first called from `core.py`.
