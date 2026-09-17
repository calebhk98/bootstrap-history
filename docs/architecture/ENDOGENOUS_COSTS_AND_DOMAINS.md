# Plan: calculated costs, and the domains that make them calculable

**Status:** proposed plan. Supersedes the sequencing sketch in `PM_ASSESSMENT.md` §5.
**Settled with the stakeholder:** the historical record must be a *plausible*
outcome, not the only one, and not one produced by feeding history back in. The
baseline is allowed to get worse while the mechanisms that will make it good
are being built.

Two goals drive everything below:

1. **Costs are calculated.** Every price, wage, and cost is computed from
   physical structure. No book values.
2. **The world has real domains.** Demography, agriculture, trade, politics,
   war, disease and the rest, interacting through one shared state.

They are the same project. You cannot calculate the price of grain without
agriculture and demography; you cannot calculate the cost of a soldier without
both plus a labour market. This document puts them in the order the
dependencies force, which is not the order either goal is usually listed in.

---

# Part 1 - What is already here

Measured against the tree on this branch, not described from memory.

## 1.1 The tree is already a physical recipe graph, mostly

This is the most important finding in this document, and it is much better news
than `PM_ASSESSMENT.md` §3.5 assumed.

| Field | Meaning | Populated | Units |
|---|---|---|---|
| `lab` | hired labour hours by trade | 89.0% | **hours** |
| `mat` | materials consumed | 65.4% | **kg / units** |
| `ph` | the founder's own hours | 94.7% | **hours** |
| `cap` | "capital beyond labour and materials" | 87.4% | denarii |
| `rev` | net revenue per year at maturity | 43.6% | denarii |
| `up` | annual upkeep once operating | 49.3% | denarii |

`lab` and `mat` are **already in physical units**, and their vocabulary is
complete: across all 2,864 nodes there are **zero labour trades and zero
materials that the price tables do not know**. That is half of an
input-output matrix, authored, validated and in the repository already.

`cap`, `rev` and `up` are denarii lumps. Those are the hardcoded prices.

## 1.1a Half, though. The tree has no production side

Run `python3 sim/audit_costs.py`. The finding that reorders this whole plan:

> **The tree records what every process CONSUMES and almost never what
> anything PRODUCES.**

| | count | share of 162 |
|---|---|---|
| distinct materials consumed somewhere in the tree | 162 | |
| ...with a node that plausibly produces them | 47 | 29.0% |
| ...where that node has a recipe of its own | 7 | 4.3% |
| ...where that node says how much it **yields** | **0** | **0.0%** |

`iron_bar_kg` is consumed by 590 nodes and **has no producing node at all**.
Nor does `timber_m3` (290 nodes), `steel_plate_kg` (236) or `coal_kg` (74).
`mat_copper` does better than most - it knows it needs 1,200 t of ore and
480 t of charcoal - and still never says how much copper comes out. Most
`mat_*` nodes are empty markers: `lab: {}`, `mat: {}`, `cap: 0`.

This matters more than anything else in this document, because **a price
cannot be solved out of a matrix with no outputs in it.** The reason every
cost in this engine bottoms out in a book value is not that `prices.json`
exists and someone likes it. It is that there is no production side to
compute a cost from, so a book is the only place a number could come from.

It also makes the job much more concrete than "make prices endogenous". The
job is: **give every consumed material a producing process with a yield.**
About 155 recipes and 162 yields. Many of the yields are derivable from
chemistry and known process efficiency - ore grade times smelting recovery -
which is exactly the class of input the no-hardcoding rule allows. It is a
large, well-specified, highly parallel authoring job, and it is the gate.

## 1.2 How much of the cost base is which

Costing the entire tree once at current book prices:

| | denarii | share |
|---|---|---|
| materials (`mat`, physical) | 15,861,856 | **73.9%** |
| capital lump (`cap`, denarii) | 5,043,903 | 23.5% |
| hired labour (`lab`, physical) | 549,829 | 2.6% |

**Three quarters of the cost base is already expressed as physical quantities.**
Pricing those endogenously converts 74% of all costs from a book number to a
computed one without touching a single node's data.

## 1.3 What the book prices are worth

`data/prices.json` holds 207 confidence-tagged entries. **190 (91.8%) are
tagged `C`, the author's own estimate.** Three are tagged `A`. The file's own
`meta.note` says the derived figures "are the weakest numbers in this project".

This is why the migration should *replace* book prices rather than run beside
them. They are not an asset whose compatibility is worth preserving.

## 1.4 What the engine does with them now

```python
buy = per_kg * 1000.0 * self.price_index * self.material_price_factor(material)
# sim/engine/economy.py:2711
```

A book value, a static per-civilisation literal that never responds to supply
or demand, and a hand-picked curve `1.0 + 0.9 * share * share`. Nothing here
clears a market.

**The curve is as much a hardcode as the price.** So is the
`0.45*food + 0.20*housing + 0.10*tools + 0.25` wage split, the per-category
`{"eta": 1.60, "floor": 0.55}` table, and the `0.9` elasticity on
`pop_deficit`. Replacing a book price with a tuned curve over a book price is
not progress, and the provenance tagging below must cover coefficients or it
will report a flattering number.

---

# Part 2 - How a price gets calculated

## 2.1 The mechanism

Take the classical linear production system. For a vector of prices `p`, an
input-output matrix `A` (how much of each good each process consumes per unit
of output), a labour-input vector `l` (hours per unit), and a wage `w`:

```text
p = A'p + w·l + rents
```

Solve for the fixed point. Prices of production fall out of the physical
structure of the economy and nothing else. This is exactly the thing the
stakeholder asked for, phrased as a solver rather than as a rule: *do not tell
me a soldier costs 100 denarii, work it back out.*

`A` is `mat`. `l` is `lab`. Both already exist.

The system needs four things the repository does not yet have:

**A numéraire.** One hour of unskilled adult labour. Every price is computed in
labour-hours; denarii are a separate layer on top. This gives the
currency-denomination invariance test from
`HISTORICAL_SIM_ARCHITECTURE.md` §11.4 for free, and makes debasement a real
mechanism instead of the scripted `real_erosion` field it is today.

**A wage.** The one price the system above cannot produce for itself. It comes
from the labour market: subsistence cost (food, shelter, fuel - themselves
priced by the system, so this iterates) against labour supply from demography
and labour demand from everything else. **This is why demography and
agriculture must exist before any cost is genuinely endogenous.**

**Rents for non-produced inputs.** Land and ore deposits are not produced, so
they have no cost of production; they earn a rent set by the extensive margin -
the quality of the worst deposit or field currently worth working. This is what
makes "a giant gold mine appears in Rome" propagate correctly with no special
case: it shifts the margin, the rent collapses, and everything downstream of
gold reprices.

**Choice of technique.** `req_any` already gives each node discrete alternative
input bundles. Pick the cheapest at current prices. The choice depends on
prices and prices depend on the choice, so it iterates alongside the main
solve. This is standard and it converges; it is also where substitution enters
a model that otherwise has fixed coefficients.

## 2.2 What this does not give you

Honestly, up front:

- **These are long-run prices of production, not market prices.** A bad harvest
  does not move them. Short-run scarcity needs a second layer: physical
  inventories, and a price that responds to the stock-to-flow ratio. That layer
  is derived from inventory dynamics rather than from an authored elasticity,
  but it is extra machinery and it comes after.
- **The matrix must be productive** (able to reproduce its own inputs with a
  surplus) or the solve does not converge. Whether this one is, is an open
  question and a cheap experiment - see Milestone 0.
- **Fixed coefficients within a technique.** Real substitution beyond what
  `req_any` enumerates is not modelled.

## 2.3 What then happens to `cap`, `rev` and `up`

Once `lab` and `mat` price themselves, the three denarii lumps are the only
hardcoded costs left, and each becomes a physical quantity:

| Field | Nodes | Becomes |
|---|---|---|
| `cap` | 2,504 | a bill of buildings, tools and land - each itself a node with its own recipe |
| `up` | 1,411 | physical maintenance consumption per year |
| `rev` | 1,249 | output quantity per year, sold at the computed price |

That is roughly 5,200 field conversions. It is real work, but it is one field
at a time, mechanically checkable, and the single most parallelisable job in
the programme - the right place to spend a large number of cheap agents.

## 2.4 The soldier, worked through

The stakeholder's own test case, to show the machinery produces it rather than
storing it:

```text
cost of a soldier-year
  = his consumption bundle          grain, cloth, fuel, priced by the system
  + his equipment, amortised        iron, leather, labour, priced by the system
  + transport and camp support      freight, priced by the system
  + the wage he would have earned   the opportunity cost of his labour
  + a risk premium                  from his actual death rate in this war
  - whatever coercion removes       conscription is an institution, not a price
```

Ten times the population moves it through the labour market. A gold mine moves
it through the money layer and the wage. Dragons eating the livestock move it
through the food price. None of those needs a branch anywhere.

---

# Part 3 - The domains, in dependency order

All sixteen requested domains belong in the destination. They do not all belong
on the critical path. Six of them **produce** the prices; the other ten
**consume** them. Building a consumer before its producer means inventing
numbers for it, which is the thing we are trying to stop doing.

| Layer | Domain | Why it must come here |
|---|---|---|
| **0** | World substrate: regions, stocks, flows, recipes, actors, ownership | Everything else needs somewhere to be and someone to own it |
| **0** | Geography and terrain | Exists as distance arithmetic; needs mutable per-region state |
| **1** | Resources and energy | Deposits with grade and depletion; the extensive margin that sets rent |
| **1** | Environment and climate (minimal) | One annual yield draw per region. Not weather |
| **2** | Agriculture and food | The surplus that decides how many people do anything else |
| **2** | Population and demography | Births, deaths, cohorts, skills. Mutually recursive with food |
| **2** | Migration | Falls out of demography plus wage differences; not a separate system |
| **3** | Economy: labour market, production, capital | **The wage, then the price solve. Costs become calculated here** |
| **4** | Infrastructure and transport | Freight cost per tonne-km from animal calories and road state |
| **4** | Trade | One market becomes many, linked by real freight cost |
| **5** | Settlement and urbanisation | Cities grow from jobs, food reach and mortality |
| **5** | Technology and research | Already strong; becomes an actor activity with actor-owned knowledge |
| **6** | Institutions and law | Rules over the above: property, tax, conscription, guilds |
| **6** | Politics and governance | The state as an organisation with a balance sheet |
| **7** | War and security | Armies as organisations consuming the same food, iron and labour |
| **7** | Diplomacy | Needs states that are real actors first |
| **8** | Disease and health | A stub at layer 2 (mortality input); a real model needs cohorts, cities and trade routes |
| **8** | Culture, religion, information | Knowledge diffusion over a real communication network |

Two things worth saying plainly about this table:

**Disease and climate get stubs early and models late.** Both feed layer 2 and
neither can be modelled properly until layers 4 and 5 exist. A stub here is an
exogenous annual draw, which is legitimate under the agreed rule: a pathogen
arriving is a scenario input, its consequences are not.

**War is layer 7 and that is not a demotion.** "Rome with rifles" is the
headline scenario, and it is precisely the one that cannot be faked. It needs
armies drawing on the same iron, grain, labour and transport as everyone else,
which means it needs all of layers 1-4 underneath it. Building it earlier means
building a combat minigame with invented numbers.

---

# Part 4 - Milestones

Each is a thing that either works or does not, with a stated measurement.

## Milestone 0 - Build the production side

**Done, in part:** `sim/audit_costs.py` now measures the gap and will keep
measuring it, so progress here has a number rather than an impression.

**The work:** every one of the 162 consumed materials needs a producing
process with inputs and, above all, a **yield**. Today 0 of 162 have one.
Author them from stoichiometry, ore grade and known process recovery - not
from a price, and not from a target cost.

Then build the matrix and try to solve. Report whether it converges, which
subgraphs are singular, and which goods still have no production path. A
matrix that is not productive - one that cannot reproduce its own inputs -
will not yield prices, and it is better to find that out on the first 20
materials than the last.

Suggested grouping, since this is the right place to spend a lot of cheap
parallel agents: metals and ores, timber and fuel, stone and ceramics,
textiles and fibres, chemicals, food and agricultural products. Start with the
six materials above that between them are consumed by 1,382 nodes.

**Nothing else in this document can start before this.**

## Milestone 1 - Provenance and a burndown number

Tag every numeric parameter with its provenance class - physical constant,
biological parameter, initial condition, calibration target, temporary
heuristic, derived. **Coefficients count**: `0.9`, `eta`, the wage split.

Ship a script that answers "what fraction of this run's output still depends on
a temporary heuristic". Today that number is close to 100% for anything
involving money. It is the only way to tell progress from rearrangement.

## Milestone 2 - The synthetic world

Per `HISTORICAL_SIM_ARCHITECTURE.md` §18: two settlements, farms, a forest, an
iron deposit, one road, differentiated workers, one government, one workshop,
one market. Layers 0-3 get built and proven here first.

Not a fork of the product. A small scenario in the same repository that new
subsystems must satisfy before they are allowed near `economy.py`.

## Milestone 3 - The `Household` extraction

Move the ~80 founder-specific attributes onto an `Actor` object; `sim.capital`
becomes a property proxying `self.founder.capital`. Mechanical, textual, and
verifiable - once `perf_fingerprint.py` can be trusted again, which it
currently cannot (see Part 5).

This is what makes a government, a firm or a second player possible, and it is
the same work for all three.

## Milestone 4 - Food and people

Agriculture and demography together, in the toy world. Land, seed, labour,
water and technique produce grain; grain and disease produce mortality; cohorts
produce the labour supply.

Acceptance: a food shortage raises mortality and wages through the ordinary
machinery, with no famine modifier anywhere.

## Milestone 5 - The wage, and the price solve

The labour market closes the system. At this point costs are calculated.

Acceptance: `data/prices.json` supplies **no material price and no wage** to
the runtime. It is retained, as validation data. The burndown script from
Milestone 1 reports 0% of material prices sourced from a book value, and the
computed Roman wage and grain price are compared against the historical record
as a check on the model rather than as an input to it.

This is the milestone that satisfies the stakeholder's first request. Given
§1.2, it converts about 74% of the cost base directly, and the remaining 26%
follows as `cap`, `up` and `rev` are converted.

## Milestone 6 onward

Transport and trade, then settlements, then state finance, then war. In that
order, for the reasons in Part 3.

---

# Part 5 - What is in the way

**`perf_fingerprint.py` does not reproduce its own recording.** This is the
most serious thing on this list, because it is the tool `sim/ARCHITECTURE.md`
names as the way to prove a change altered nothing, and it currently cannot
prove it. Milestone 3 must not start behind it.

The evidence, all from a pristine checkout of `origin/main` with no local
changes:

| Run | Result |
|---|---|
| record, then check against itself | `FAIL: 2 of 9 diverged` - rome/seed1 at year 106, england/seed1 at year 97 |
| record twice, diff the two recordings | `1 of 9 diverged` - mexica/seed1 at year **7** |

Same code, same seeds, same machine. A different scenario and a different
year every time.

### What has been ruled out

Recorded so the next person does not repeat it:

- **Hash-seed randomisation.** One scenario run alone in a fresh process gives
  a byte-identical digest across three runs with `PYTHONHASHSEED` unset and
  three with it fixed at 0.
- **Mutation of the shared tree.** `NODES` and `ORDER` hash identically before
  and after six scenarios run against them. No `Sim` class attribute is
  created or mutated either.
- **The `id()`-keyed cache in `_revenue_upkeep_candidates`** (`economy.py`
  around line 2110). This looked like the answer: `id()` is a memory address,
  a freed object's address can be reused, and `sim/engine/proto/nodes.py`
  documents that exact hazard and defends against it by holding a strong
  reference while the three other `id()`-keyed caches in the engine do not.
  A probe that recomputed the true answer on every call and compared it with
  the cached one found **0 stale answers in 64,157 calls** across all nine
  scenarios. The hypothesis was wrong. (Caveat: the probe allocates, which
  perturbs exactly the allocator state the hazard depends on. It is weak
  evidence, not a clean bill of health, and `_DESC_CACHE` in `data.py` around
  line 285 - validated only by `len(nodes)` - remains unexamined.)

### What is still open

Whether the divergence accumulates within a process as scenarios run, or
whether each process is internally consistent and something process-global
differs between them. The experiment is one run of the reference sequence
twice in the same process, comparing the two passes.

This deserves its own focused session. It is a correctness question about the
simulation, not only about the test tool: something in this engine returns a
different answer for the same inputs, and a simulator whose costs are supposed
to be calculated cannot afford that.

**The test suite has never run to the end.** Fixed on this branch - see the
previous commit - but worth remembering as a prior on the rest of the
infrastructure: the green light had been partly decorative for a long time.

**`protocol.py` is unguarded.** Roughly a third of the code, covered by neither
`perf_fingerprint` nor anything else that proves behaviour. Milestone 3 touches
it.

**Scope.** Sixteen domains is a destination. Six of them, done properly, is a
year of work that produces a simulator that calculates its own costs. Starting
all sixteen produces sixteen stubs and no prices.
