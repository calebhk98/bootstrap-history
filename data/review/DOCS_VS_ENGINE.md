# Lore vs engine: mechanics the documentation describes and the code does not do

The owner's own read of this project, after looking at the prose rather than
the tree: "the lore in a lot of it looks like things we may want implemented."
This file is that search, done properly. For every passage below I read the
passage, then went and checked the engine (`grep`, a targeted `Read`, or a
short verification script against `rome/data/tech_tree.json`) before writing
down what it actually does, not what seemed plausible. Passages I could not
verify one way or the other are left out rather than guessed at.

Ranked by how much building the mechanic would add to the simulation, most
valuable first. Effort is a rough shape (small/medium/large), not an
estimate in hours - this project's own convention for its cost figures.

---

## 1. A rival-imitation model is fully built and tested, and never costs the founder a denarius

**The passage, and where it gets interesting: the code documents the promise
better than the prose does.** `rome/sim/engine/society.py:765-807`,
`diffusion_share()`'s own docstring: "how much of what running venture `k`
earns **has already leaked to competitors who watched you run it and went
into the same business themselves**... a `corpus` that is written down and
dispersed is knowledge a rival can read rather than having to
reverse-engineer from watching your workshop... **FOR THE MARKET AGENT: a
revenue formula that wants to spend this number honestly should reduce what
THIS venture earns by up to this share**." That is a design brief embedded
in the source, describing exactly the mechanic the knowledge corpus's law
and property section keeps gesturing at without ever naming a number for:

- `rome/knowledge/96_finance.md:361` - patents: "a temporary monopoly in
  exchange for PUBLICATION... forcing inventors to share their secrets."
- `rome/knowledge/96_finance.md:407` - trademarks: "a competitor cannot use
  the mark without facing legal action."
- `rome/knowledge/95_expeditions.md:161` - "you can pay for a monopoly
  legally... ensuring the sellers do not sell to competitors."
- `rome/data/world/COMMODITIES.md:380` - `monopoly_possible: true` on
  coffee, "the flag is advisory, not enforced."

**What the engine actually does, verified.** `diffusion_share(k)` and
`diffusion_index()` (`society.py:765,809`) are real, fully implemented, and
thoroughly regression-tested (`test_regressions.py:6966-7022`: zero for
anything not operating, zero for anything with no revenue, rises with time
operated, rises faster once `corpus_dispersed` is running, is reported in
`state` between 0 and 1). Grepping every consumer of `diffusion_share`
(`grep -rn diffusion_share rome/sim/engine/*.py`) turns up exactly four call
sites: the two tests, `diffusion_index()`'s own internal average, and
`protocol.py:508`, which puts the number in the `state` object a player can
read. **`economy.py`'s `revenue()` and `revenue_sources()` never call
either function.** A venture's actual income is computed from `rev`,
`venture_ramp()`, `output_factor`, `price_index` and `goods_market_factor()`
alone (`economy.py:1173` onward) - `diffusion_share` is a sensor with no
actuator wired to it. The docstring says exactly why: it was deliberately
left unwired pending a decision about which "agent" (which code path) should
own spending it, and that decision was never made. Separately, and for the
same underlying reason: nothing in `diffusion_share()` reads
`fin_patent_office`, `fin_trademark` or `collegium_licensed` at all, so even
once it IS wired in, the patent/trademark/guild-licence cluster the
knowledge corpus describes as protection against exactly this has no lever
to pull.

**How big a job, and is it worth it.** Small - genuinely small, which is
the finding. The hard modelling work (a saturating, literacy- and
publication-sensitive erosion curve, tested against edge cases) is already
done and already green in the regression suite. What is missing is one line
in `revenue_sources()` (`amt *= (1.0 - self.diffusion_share(k))` alongside
the existing `goods_market_factor(k)` multiply) and a handful of new
regression checks proving revenue actually falls as `diffusion_share` rises.
Extending it to read the patent/trademark/licence nodes as a brake on the
erosion rate (the same shape `corpus_dispersed` already uses to accelerate
it, just negative) is a second small step, not a redesign. **Recommended
first**: it is the cheapest item on this whole list, because someone already
did the expensive part and stopped one commit short of spending it.

---

## 2. The game already knows the plague is coming. Prices do not.

**The passage.** `rome/data/world/COMMODITIES.md:610-615` (section 10, point
5): "A currency debasement, a mine flooding, a war closing a trade route:
each is a real, dateable price event in this simulator's own period (**the
model already has `SHOCKS` in `data.py` for plagues and debasement**). None
of them currently move a commodity price. Wiring `SHOCKS` into
`price_with_noise()`'s mean is straightforward in principle and untouched
here."

**What the engine actually does.** Verified: `SHOCKS` is real
(`rome/sim/engine/data.py:428`, `antonine_plague=(165,180)`,
`cyprian_plague=(249,262)`, `third_century_crisis=(235,284)`,
`debasement_starts=190`) and is imported by every engine module. It drives
`staff_loss` and `output_factor` hazards in `core.py`/`society.py`. It is
never imported by `commodities.py`, and `price_with_noise()`/`price_series()`
(`commodities.py:263,278`) apply only a flat Gaussian wobble around the
supply/demand fundamental - a debasement year and a peaceful year price
identically.

**How big a job, and is it worth it.** Small - the doc's own author already
scoped it as "straightforward in principle." The founder in this game is
explicitly written to know the plague dates in advance (`ROME_BOOTSTRAP.md`:
"You know when the plagues come. Nobody else does. That is worth more than
any machine in this document") - a price signal that actually spikes ahead
of a dateable shock is exactly the kind of edge that premise sets up and the
market layer currently cannot pay off. **Recommended**: cheap, and it
connects a mechanic the game's own premise advertises to a system that
already tracks everything it needs.

---

## 3. Nothing you produce outlives the year you produced it

**The passage.** `rome/data/world/COMMODITIES.md:502-510` (section 8): "**Your
stock on hand**: a running balance of what you have produced or bought minus
what you have consumed or sold. `commodities.py` provides a minimal `Ledger`
class for this... but nothing in the existing `Sim` currently calls it: `Sim`
has never modelled an inventory, only annual flows netted against each other
within the same year. Wiring a real stockpile into `Sim` (so unsold cloth
carries over, so a mine's output that exceeds this year's building programme
accumulates rather than evaporating) is second-pass work."

**What the engine actually does.** Verified: no `on_hand`, `inventory` or
`warehouse` concept anywhere in `core.py` or `economy.py`. A mine that
produces more ore than this year's active projects can use does not bank the
surplus for next year; it is simply not consumed. A founder who, knowing the
Antonine Plague arrives in 165 AD, tries to stockpile grain or medicine
ahead of it in 163 AD has no lever to pull - the model has no concept of
"stockpile" for them to pull it with.

**How big a job, and is it worth it.** Medium-large - this touches the core
year-loop's accounting, not an isolated function, and every material-demand
call site (`resource_throttle`, `annual_material_demand`) would need to
check a stock before falling back to a flow. Worth doing eventually, but
lower priority than #1 and #2: most players do not notice a flow model
unless they specifically try to bank ahead of a known date, which is a
narrow (if thematically resonant) use case. **Worth scoping, not urgent.**

---

## 4. A shortage of smiths never shows up as a shortage of wire

**The passage.** `rome/data/world/COMMODITIES.md:535-540` (section 9): "**No
labour throughput ceiling on manufacturing.** `copper_wire`'s supply is
capped by copper availability and by a flat technology multiplier, not by
how many smiths exist to draw it. The wage/labour-market machinery in
`sim/engine/labour.py` is a whole parallel system this framework does not
touch. A finished good that is short on LABOUR rather than material is a
real and common failure mode this pass cannot represent."

**What the engine actually does.** Verified against `propagate_demand()`
(`commodities.py` section 7): at a manufactured commodity, the function
compares its own production capacity (a flat multiplier from the built
technology) against what its input commodities delivered - it never reads
`self.employees`, `craft_hands_available()`, or any other value from
`labour.py`, even though `labour.py` is a fully built, heavily used system
everywhere else in the game (staff counts, training lag, wage pressure,
attrition all live there).

**How big a job, and is it worth it.** Medium - `propagate_demand()` already
has the shape (compare capacity against delivered input, report whichever
binds), so adding a third comparison against `craft_hands_available()` for
the relevant trade is mostly plumbing, not new design. Worth doing: it
closes the gap between two systems (`labour.py` and `commodities.py`) that
the project has already invested heavily in separately, and "you have the
copper but not the smiths" is a genuinely different, genuinely interesting
failure mode from "you have the smiths but not the copper," which the
`el2_` electrical branch's 36 real wire-drawing nodes would actually
exercise.

---

## Smaller items, noted but not ranked at length

- **Nobody competes with you for materials, and no war targets you
  specifically.** `rome/data/world/COMMODITIES.md:541-544` - "No competing
  buyers... There is exactly one demand source in this model: you";
  `rome/sim/ECONOMY_GENERALIZATION_NOTES.md:74` - "No multi-agent market...
  this remains a solo-player economy against a static empire backdrop";
  `rome/02_STRATEGY.md:331` - "There is no competitor, no state seizure of
  your industry, and no war that targets you specifically." Verified true
  (`resource_throttle()` checks your demand against total national output
  with no other buyer subtracted). This is a different, and much larger,
  gap than #1 above - it is about the whole empire's competing claims on
  iron, silver and grain, not one rival copying one venture - and this
  project's own design notes already treat a full version of it as
  correctly out of scope (a second simulation). Not ranked as its own item
  because the honest verdict, already reached by the project itself, is
  large effort for a diffuse gain; #1 gets most of the same narrative payoff
  ("someone else is watching what you do") for a fraction of the cost.
- **Regional trade in the standalone commodity layer is Roman-calibrated
  regardless of who is asking** (`COMMODITIES.md` section 6/10.6): a Norse
  and a Roman player get the identical `trade_partners()` answer from
  `commodities.py`, even though the live `Sim.material_reach()` already
  varies convincingly by civilization and is already used for exactly this
  purpose elsewhere. Small effort - the seam is already named
  (`reach_fn: Callable[[str], int]`) - but low value until `commodities.py`'s
  general functions are wired into the live game at all, which they
  currently are not (only `propagate_demand()` is, per section 0).
- **Reputation rewards building, not running**
  (`rome/playtest/TASKS_open.md:17`, still open as of this pass): the
  completion reward reads state interest, tier and revenue and never checks
  `operating`, so it can be maximised by building things and never opening
  them. Small effort (the codebase already has the `running()` vs `has()`
  distinction used correctly elsewhere, e.g. `military_leverage()`), and
  worth fixing because it directly contradicts what the rest of the design
  says reputation is for - `rome/knowledge/03_SOCIAL_POLITICS.md` describes
  reputation as earned by "visible, useful, State-approved work," which
  reads as ongoing, not a one-time completion bonus.
- **Seasonal commodity price variation and one-off shocks like a mine
  flooding** (`COMMODITIES.md` section 4.4) are real gaps but low value:
  the noise term already gives a market year-to-year texture, and a full
  seasonal model is a lot of new machinery for a cosmetic improvement.
- **By-products and joint production** (`COMMODITIES.md` section 10.3 - a
  copper mine also yields silver and arsenic) is real and honestly scoped by
  its own author as needing a cycle-safe recipe graph first; not worth
  building ahead of items 1-4 above.

---

## Top recommendation, stated plainly

If only one of these gets built: **#1 (wire `diffusion_share()` into
revenue)**. It is the cheapest item on this list by a wide margin - the
hard part is already written, tested and sitting one `import` away from
`economy.py` - and it is the one that makes a whole cluster of existing,
currently inert nodes (patent, trademark, professional exam, monopoly,
guild licence) do something for the first time. If two get built, add
**#2 (wire `SHOCKS` into commodity prices)**: also small, also fully scoped
by the project's own design note, and it pays off a promise the game's
premise makes explicitly ("you know when the plagues come").
