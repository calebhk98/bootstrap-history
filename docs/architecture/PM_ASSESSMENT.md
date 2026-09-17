# PM assessment of the two architecture documents

**Reviewing:** `HISTORICAL_SIM_ARCHITECTURE.md` (the target model) and
`CURRENT_CODE_ARCHITECTURE_REVIEW.md` (this repo measured against it).
**Status:** assessment and proposed sequencing. Not yet an approved plan.
**Every number below was measured against the tree as it stands on this
branch**, not taken from either document.

---

## 0. Verdict in one paragraph

The target document is a good north star and its testing chapter is the most
valuable thing in either file - adopt it close to wholesale. The review
document is about 70% right and I want to keep most of it, but its central
recommendation ("expand in place, keep everything live, no parallel engine")
is asserted rather than argued, and the measurements below contradict it on
the one step that matters most. The review also does not engage with the
actual blocking problem, which is not architecture at all: **the stakeholder
has given us two requirements that cannot both be satisfied as literally
stated**, and until that is resolved, any phase plan is guesswork.

---

## 1. What I measured first

Before agreeing or disagreeing with a review of this codebase, I had the
codebase measured. Findings, with citations, because the rest of this document
leans on them:

### 1.1 Prices are book values, not outcomes

`data/prices.json` holds 207 confidence-tagged entries. **190 of them (91.8%)
are tagged `C` - "author's estimate or inference".** Only 3 are tagged `A`.

The runtime price of a material is:

```python
buy = per_kg * 1000.0 * self.price_index * self.material_price_factor(material)
# sim/engine/economy.py:2708-2711
```

where `per_kg` is the flat book number, `price_index` is a **static literal
read once from the civilisation file** (`core.py:55`; Rome 1.0, Han 0.75,
Norse 1.4) that never responds to supply or demand, and the demand term is a
hand-picked curve:

```python
share = min(1.5, need / supply)
worst = max(worst, 1.0 + 0.9 * share * share)
# sim/engine/economy.py:3377-3379
```

Wages have the same shape: a base derived from `prices.json` by literal
conversion constants (`data.py:126`, `day_hs / 4.0 * 250.0`), multiplied by
fixed budget-share weights (`0.45*food + 0.20*housing + 0.10*tools + 0.25`,
`labour.py:1025-1026`), the same static `price_index`, a `wage_index` that
moves only with population deficit (`core.py:424`, elasticity literal `0.9`),
and the identical `1 + 0.9·share²` scarcity curve (`labour.py:272-273`).

**Nothing in the engine clears a market.** There is no quantity supplied and
quantity demanded meeting at a price. There is a book price with authored
elasticity curves bolted on.

### 1.2 The historical trajectory is typed into the civilisation files

Hazard counts: Rome 17, England 19, Mexica 17, Han 13, Norse 8. Each entry is
a fixed year window plus fixed magnitudes:

```json
{"name": "Antonine plague", "staff_loss": 0.28, "years": [165, 180]}
{"name": "Third century crisis", "output_factor": 0.62, "sack_chance": 0.16,
 "values": {"w_religious_rigidity": 0.15}, "years": [235, 284]}
```

The engine gate is `if not (a <= yr <= b): continue` (`society.py:2184-2186`).
A further 32% annual fire-chance and the sack damage fractions (0.60 capital,
0.55 artisans, 0.55 scholars, 0.65 directors) are literals in the engine
itself. What *is* emergent is how much of the fixed magnitude is mitigated by
what has been built.

To the project's credit, this is all data rather than `if year == 476`, and a
few hazards carry `condition.requires_all` tech gates that can avert them. But
the shape is unambiguous: **the reason the baseline resembles our timeline is
that our timeline is in the input file.**

### 1.3 Population is one scalar

`pop_scale` plus a `pop_deficit` that decays exponentially with
`tau = max(10, recovery_years) / 3` (`core.py:392-396`), the recovery horizon
calibrated off England's Black Death. No cohorts, no births, no deaths, no
migration.

### 1.4 There is no actor concept at all

Grep across `sim/engine/` for `owner`, `actor`, `faction`, `organization`,
`agent_id`: **zero fields.** The only hits are prose in comments. `sim/
ECONOMY_GENERALIZATION_NOTES.md` states it outright: "This remains a solo-
player economy against a static empire backdrop."

Known technology is two flat sets on `Sim` - `self.done` (you built it) and
`self.granted` (society already had it) - with `def has(self, k): return k in
self.done` (`core.py:447-448`). Material stock is one flat `Counter` keyed by
material with no owner or location dimension (`economy.py:2684-2696`). Mines
are a bare list. Geography holds no mutable per-region state whatsoever; it is
pure distance-to-multiplier arithmetic over a read-only JSON.

Of the 157 `Sim` attributes, roughly **78-80 are founder-specific** and would
have to become per-actor to support a second owner; counting the caches keyed
off them, realistically 95-100. That is the same refactor `sim/ARCHITECTURE.md`
already considered and rejected, in its words, as "a rewrite of most of 30,000
lines."

### 1.5 Every tech node carries authored cost and revenue

All **2,864 nodes** carry `cap`, `rev`, `up`, `lab`, `mat`, `risk`,
`adopt_yrs`, `ph`, `sch` and `art`. Not some. All of them.

### 1.6 Baseline health

`1498 checks, 0 failures, 66s` across 42 test topics. The suite only runs if
the checkout directory is named `rome/`; in a directory named
`bootstrap-history` it dies on `ModuleNotFoundError: No module named 'rome'`.
Minor, but it should be fixed before anyone builds CI on it.

---

## 2. Where the review document is right

I want to keep these and I do not think they are seriously arguable:

1. **Do not throw away the tech tree.** 2,864 nodes with capability rungs,
   `req_any` substitutions and `kb` links into a written procedure library is
   the single most valuable asset here and the hardest thing to rebuild.
2. **Do not solve generalisation by making the founder less detailed.**
   Correct, and it is the failure mode most likely to be proposed by someone
   who has read the target document and not the code.
3. **Ownership belongs at the centre of the model.** Also correct, and it is
   the same work as actor-specific knowledge, state-as-an-actor, and
   eventual multiplayer - see §5.
4. **Knowledge, skill, ownership of the machine, and ability to reproduce the
   machine are four different states.** This is the intellectual core of both
   documents and it is right.
5. **Tag parameter provenance.** Cheap, and it converts "stop hardcoding
   things" from a vibe into a burndown chart.
6. **Historical data splits into initialisation / calibration / validation /
   scenario-event / should-be-endogenous.** This is the correct framing and
   §9 of the review states it well.
7. **Keep the CLI/JSON protocol, the explainability commands, the deterministic
   seeds and the complaint-to-regression-test habit.**

---

## 3. Where I disagree with the review

### 3.1 "Expand in place, no parallel engine" is asserted, not argued

The review states this in its executive summary and repeats it as the bottom
line, but it never examines the coupling that would have to be paid for. The
measurements in §1.4 say its own Phase 2 ("generalise ownership") *is* the
30,000-line refactor this repo already evaluated and declined. Renaming a
rejected refactor into a phase does not make it cheaper.

The review's Phase 1 has the opposite problem: adding `WorldState`,
`Organization`, `Facility` and `PopulationCohort` containers that "initially
mirror current values" and change no behaviour is genuinely free, and it is
also genuinely worthless. Empty containers do not constrain anything. The
acceptance criterion it proposes - "existing tests remain green and gameplay
behaves the same" - is satisfied by writing zero useful code.

**What I think the right answer is, which neither document names clearly:** a
mechanical `Household` extraction. Move the ~80 founder attributes onto an
`Actor` object, give `Sim` a `self.founder`, and keep `sim.capital` working as
a property that proxies `self.founder.capital`. That is a scriptable,
diff-reviewable, `perf_fingerprint`-verifiable change - it is textual, not
semantic, and it does not require any call site to be re-reasoned. It is
perhaps 10% of the cost of the "give 157 fields explicit owners" rewrite and
it buys the entire actor axis. It is the one large refactor I would actually
approve.

### 3.2 The compatibility-shim strategy is the wrong default for prices

The review's repeated pattern - keep the old scalar, make it a derived
summary, remove it later - is sound for population and state capacity. It is
the wrong call for prices, and the reason is §1.1: **92% of the price data is
the author's own admitted guesswork.** The review treats the book prices as an
asset whose compatibility is worth preserving. They are not an asset. They are
the largest single source of error in the project, and the author says so in
the file's own `meta.note`.

Where a derived price is available, it should replace the book price outright
rather than run beside it. Two live pricing systems with a reconciliation
layer, guarded by 42 test topics that assert on the old one, is how this
program stalls.

### 3.3 Both documents are soft on the fact that a tuned curve is a hardcode

The stakeholder's rule, as reported, is "no `agricultural_productivity_modifier
= 0.85`". The review's §10 dutifully lists prices and indices as migration
targets. Neither document says clearly that `1.0 + 0.9 * share * share` is
exactly the same category of object. So is the `0.45/0.20/0.10/0.25` budget
split. So is the per-category `{"eta": 1.60, "floor": 0.55}` table. So is the
`0.9` elasticity on `pop_deficit`.

Replacing a hardcoded price with a hardcoded curve over a hardcoded price is
not progress against the requirement, and we should not let ourselves report
it as progress. The provenance tagging in review §11 must cover coefficients,
not just values, or it will produce a flattering number.

### 3.4 Physical quantities are the hard dependency, and the review buries it

You cannot clear a market without quantities on both sides. This simulation
currently has, in physical units, one `Counter` of the founder's material
tonnes. The rest of the economy has no production volume and no consumption.
The review gets the ordering right (its Phase 3 precedes Phase 4) but presents
it as one phase among eleven. It is not. **Physical accounting is the gate
that everything endogenous sits behind**, and roughly half the review's
remaining phases are unreachable until it exists.

### 3.5 The cost of re-deriving 2,864 nodes is not mentioned anywhere

Review §12 calmly says `cap` becomes derived, `rev` becomes derived, `up`
becomes explicit maintenance consumption, `risk` becomes derived, `adopt_yrs`
gets replaced by diffusion behaviour. Every one of the 2,864 nodes carries
every one of those fields (§1.5). Deriving them means re-authoring what those
fields mean - from "the price of this project" to "the physical inputs this
process consumes" - across the whole tree.

That is plausibly the largest single work item in the entire programme and
neither document costs it. It is also the item most amenable to farming out to
cheap parallel agents, which is the one piece of good news about it.

### 3.6 Neither document addresses multiplayer, which is a missed simplification

The brief mentions multiple players eventually. Neither document engages with
it. This is worth saying explicitly because it *raises* the priority of the
actor work rather than adding a new workstream: multiplayer is not a separate
feature, it is the actor axis plus a decision about turn resolution order.
The same change serves the founder scenario, the "rich state doing research
blindly" scenario, knowledge diffusion, state-owned workshops, and
multiplayer. That makes it the highest-leverage item in the programme by a
wide margin, and it is the argument for paying for the `Household` extraction
in §3.1.

---

## 4. The contradiction that has to be resolved before any plan is real

Two requirements as reported:

- **A.** No hard inputs. If there are ten times as many people, or a gold mine
  appears, or dragons exist, the price of a soldier must move. Applied to
  everything.
- **B.** Without the intervention, the simulation should play out roughly like
  our timeline.

Taken literally, these are incompatible, and the incompatibility is not a
detail to be engineered around. Our timeline is one draw from a
high-variance process. A genuinely endogenous model of the Roman economy does
not reproduce the Antonine plague in 165 AD; it produces epidemics whose timing
depends on contact networks and pathogen introduction. If the baseline still
reliably yields the Third Century Crisis at 235, that is proof we cheated.

**The reconciliation I would take back to the stakeholder**, which I believe is
what they actually want:

> The historical record should be a **plausible draw from the baseline
> ensemble**, not the median path of a single run. We validate against
> distributions and relationships - population ranges, urbanisation share,
> wage-to-grain ratios, army scale, technology appearance windows - not against
> dated events. Scenario events (a pathogen arriving, an external army that we
> do not simulate the homeland of) remain legitimate injected inputs, but their
> consequences are resolved by the normal machinery rather than specified.

If the stakeholder agrees to that, the programme is hard but coherent. If they
insist the baseline must hit the Antonine plague in 165, then the honest answer
is that we keep a scripted event layer permanently and we should stop pretending
otherwise in the architecture documents. **This is the single question I most
need answered**, and it costs nothing to ask.

A second, smaller question worth asking at the same time: what is the appetite
for the baseline getting *worse* before it gets better? Every step toward
endogeneity will, in the short run, produce a baseline that matches history less
well than the current scripted one does. There is no path that avoids this.

---

## 5. Proposed sequencing

Adopting the target document as the north star and about 70% of the review,
reordered around the measurements above. This replaces the review's eleven
phases, which are a domain list rather than a critical path.

**Step 0 - resolve §4 with the stakeholder.** Costs a conversation. Blocks the
meaning of every acceptance test downstream.

**Step 1 - provenance tagging and a burndown script.** Tag every numeric
parameter, *including curve coefficients*, with its provenance class. Ship a
script that reports what fraction of a given run's output depends on temporary
heuristics. This makes the requirement measurable, it is cheap, it is
parallelisable across many small agents, and it is the only way we will ever
know whether we are making progress against requirement A rather than moving
the hardcoding around.

**Step 2 - the synthetic vertical slice**, per target document §18: two
settlements, farms, a forest, an iron deposit, one road, differentiated
workers, one government, one workshop, one market. This is where I part from
the review's "no parallel simulator" rule, and I want to be precise about how
far: we are **not** forking the product. This is a small scenario inside the
same repo that new subsystems must satisfy, and it exists because developing
market clearing inside a 4,350-line `economy.py` guarded by 1,498 assertions
about book prices is a way to fail slowly. Every mechanism below gets built
against the toy world first and promoted into the main world second.

**Step 3 - the `Household` extraction** (§3.1). Mechanical, proxy-guarded,
verified by `perf_fingerprint`. Unlocks the actor axis, therefore the state as
an actor, therefore knowledge diffusion, therefore multiplayer.

**Step 4 - actor-scoped knowledge.** `self.done` / `self.granted` become
per-actor. This is small once Step 3 exists and it immediately delivers the
scenarios the brief actually asks about: the founder knows something the state
does not; the state can be taught, can buy, can steal, can fail to understand.

**Step 5 - physical accounting on one narrow chain** (§3.4), end to end, in the
toy world: `farm → grain → transport → city consumption` or
`forest → charcoal → iron → tools`. Real inventories, real labour hours, real
facilities. Invariant: no output without accounted inputs.

**Step 6 - a clearing market on that one chain**, replacing rather than
shadowing the book price for those goods.

**Step 7 onward** - population cohorts, then settlements, then state finance,
then endogenous conflict - in roughly the review's order, which is sound once
the gate at Step 5 is open.

The tree re-derivation (§3.5) runs as a continuous background effort from
Step 5 onward, farmed out in branch-sized chunks, since it is the largest and
most parallelisable single item.

---

## 6. Risks I want on the record

1. **The baseline will get worse before it gets better.** Guaranteed, not a
   risk to be mitigated. Needs to be agreed up front (§4).
2. **The existing test suite encodes the current abstraction.** 1,498 checks,
   many asserting on book-price outputs. The review is right that these should
   be reclassified rather than deleted, but reclassifying 1,498 assertions is
   itself real work nobody has costed.
3. **`perf_fingerprint.py` does not cover `protocol.py`**, where roughly a
   third of the code lives. Any refactor touching the protocol layer is
   unguarded. This should be fixed before Step 3, not during it.
4. **Scope inflation is the most likely way this dies.** The target document
   lists 20 domains. Delivering 6 of them properly beats starting 20.
5. **Effort.** I am not going to pretend to a schedule. What I will say is that
   Steps 0-2 are small, Step 3 is one large but mechanical refactor, and Steps
   5-6 are genuine research-grade modelling work whose duration nobody can
   honestly estimate until the toy world exists. That is the reason the toy
   world comes before the estimate.
