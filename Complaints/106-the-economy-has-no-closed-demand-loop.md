# The live economy lacks a closed population/income/demand loop

**Source:** playtest findings document, ECON-004. **Status:** Architecture
finding with substantial existing groundwork; do not read this as "build a
demand model," because one already exists. Read it as "wire the one that
exists in."

## The player's point

Late-game revenue in the live engine comes from `base venture revenue *
generic market/economy factors`, not from a chain of population, income
distribution, prices and preferences producing final demand, plus industrial
production plans producing derived intermediate demand, with supply and
demand together setting prices and quantities. The player's phrasing of the
open question: "who is actually buying 20 million denarii a year of final
goods, at what incomes and prices?" Their write-up correctly notes that
`sim/world/demand.py` already contains a much richer demand model (Stone-
Geary/LES household demand, income distribution, derived intermediate
demand, joint-product value allocation, market-clearing logic) and that its
own header says it is standalone and does not close the full engine loop.

## What already exists, checked directly

This is the central thing to get right here, because a complaint that says
"build a demand model" when one already exists would be actively
misleading, and CLAUDE.md's own task brief for this review flagged exactly
that risk.

`sim/world/demand.py`'s own module docstring (read in full) confirms the
player's summary: it builds household demand via a Stone-Geary/Linear
Expenditure System with a subsistence floor and marginal budget share per
good, splits households into income bins from a Gini coefficient via a
Pareto distribution, and computes derived (intermediate) demand straight
from `data/production/*.json`'s own `inputs` and `capital.build_materials`
fields, scaled by whatever output level a caller reports. It also computes
joint-product value shares, the mechanism `Complaints/29` (open,
"Joint production has no cost-side answer") identified as the missing
piece for splitting one furnace cost across two outputs (lead and silver).

**Wiring status, verified by grep, not assumed:**

    grep -rn "world.demand\|world import demand\|from world.demand" sim/engine/ sim/solve_prices.py
    -> no matches

`docs/architecture/STATE_OF_THE_PROJECT.md` (Part 2, its own import table)
confirms this independently: "`demand.py` imported by NOTHING under
`sim/engine/` or `sim/solve_prices.py`." Of the eight `sim/world/` domain
modules, five (agriculture, demography, land, transport, military_logistics)
are wired directly into the engine; a sixth (deposits) is reachable only
through the solved-price path, which is off by default
(`sim/engine/data.py`'s `use_solved_prices` is confirmed `False`); and two
(demand, labour_market) are wired into nothing at all. `demand.py` is one of
those two.

`sim/world/labour_market.py` is the companion piece the player's ECON-004
write-up does not name directly but which the same architecture document
identifies as the other half of a closed loop: it computes hours a trade
NEEDS from planned output versus hours the workforce actually HAS, and
nothing in the live engine calls it either. `sim/engine/labour.py` still
prices every trade off a static `TRADE_DENSITY` classification that never
moves with another trade's fortunes.

## How this sits against CLAUDE.md and the architecture plan

This is not a gap the project has overlooked; it is a gap the project has
already measured and sequenced. `docs/architecture/STATE_OF_THE_PROJECT.md`
Part 4 ("What to do next, in order, and why") lists wiring
`sim/world/labour_market.py` into the engine as its #1 recommendation and
wiring `sim/world/demand.py` into `sim/solve_prices.py` (replacing the
current mass-split joint-byproduct allocation) as its #2, both described as
"a wiring job, not a design job" because the modules are already built and
tested standalone. This complaint's contribution is corroborating that from
the player's independent playtest angle (a concrete "who buys 20M denarii of
output" question) rather than proposing new work; the honest framing for
whoever picks this up is "finish a plan already on record," not "start a
new one."

§3.5 (no save migrations) is worth stating explicitly because wiring in a
persisted `Workforce` object (labour_market's own state) is exactly the kind
of change that tempts a migration plan: it does not need one. A field added
to `SAVE_FIELDS` in this build works within this build; there is no
obligation to load an old save that predates it, per §3.5.

## Cross-references

`ARCH-001` (`Complaints/119`) makes the same "multiple parallel models"
point about these same three modules from an architecture-hygiene angle
rather than a realism angle; read the two together. `Complaints/29` (joint
production underdetermined) and `Complaints/32` (capital is not the gap,
rent is) are the two complaints `demand.py`'s own module docstring cites as
its reason for existing. `docs/architecture/DEMAND_AT_SCALE.md` already
reviews whether the household-demand model holds outside Roman Egypt.

## Size

This is a multi-month wiring and calibration effort even though the core
mechanism already exists in code: it touches `sim/engine/labour.py`,
`sim/solve_prices.py`, `SAVE_FIELDS`, and needs new engine-side calls
(comparable in scope to the Milestone 4 agriculture/demography wiring the
architecture document describes). Treat this as a roadmap entry that already
has a design and a sequencing plan, not a fix-sized task.
