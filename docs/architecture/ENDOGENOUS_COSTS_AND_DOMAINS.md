# Plan: calculated costs, and the domains that make them calculable

**Status:** design direction. What is built, and what is measured about it, is in
`STATE_OF_THE_PROJECT.md` (its commands, not this file, say how far each part is). What is open is in
`Complaints/` (`grep -m1 '^\*\*Status' Complaints/*.md`).
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

# Part 2 - How a price gets calculated

## 2.1 The mechanism

Take the classical linear production system. In the textbooks it is written
`p = A'p + wl + r`, which is four letters standing for four things nobody can
recover without the textbook. Written out, the price of any good is:

```text
price_of(good) =   sum over each input of
                       quantity_consumed_per_unit(good, input) * price_of(input)
                 + sum over each trade of
                       hours_per_unit(good, trade) * wage_of(trade)
                 + rent_per_unit(good)        # land, ore deposits: not produced
```

A good's price is what it takes to make one of it: the inputs at their own
prices, the labour at its wage, and rent on anything nature supplied rather
than a process. Every one of those prices is defined the same way, so this is
a system of equations rather than a lookup, and you solve it for the fixed
point where every price is consistent with every other.

That is exactly what the stakeholder asked for, phrased as a solver rather
than as a rule: *do not tell me a soldier costs 100 denarii, work it back
out.*

The two hard parts are authored data. `quantity_consumed_per_unit` is the `inputs` of an entry in
`data/production/` and `hours_per_unit` is its `labour_hours`, by trade; the field list is
`data/production/_SCHEMA.md`. A tree node's own `mat` and `lab` are what building it consumes.

Code written against this should spell the names out. `prices_by_good`,
`input_quantities`, `hours_by_trade`, `wage_by_trade`, `rent_by_good` - not
`p`, `A`, `l`, `w`, `r`. The compression is a convention of printed economics
papers with a symbol table on page one, and it has no place in a codebase that
several agents and one human have to keep straight between them.

The system needs four things beyond the recipes:

**A numéraire.** One hour of unskilled adult labour. Every price is computed in
labour-hours; denarii are a separate layer on top. This gives the
currency-denomination invariance test from
`HISTORICAL_SIM_ARCHITECTURE.md` §11.4 for free, and makes debasement a real
mechanism instead of a scripted `real_erosion` hazard.

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
  question; `python3 sim/simulator.py validate` and the solver's own convergence report say.
- **Fixed coefficients within a technique.** Real substitution beyond what
  `req_any` enumerates is not modelled.

## 2.3 Capital, upkeep and revenue of a node

A node's capital (`cap_hours`) and upkeep (`up_hours`) are stated in hours or derived from its staff and plant
(`sim/content/node_defaults.py`); revenue is the output of the entries that name the node in `operated_by`
(`STATE_OF_THE_PROJECT.md` row 5). Nodes that make nothing earn nothing: `Complaints/510`.

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
| **0** | Geography and terrain | Per-tile state the other domains read (`sim/geography/`) |
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

# Part 4 - Where each part stands

Not kept here; it goes stale. Use `STATE_OF_THE_PROJECT.md` (milestones, each with its measuring command) and these:

    python3 sim/simulator.py validate        the production data: every consumed material has a producing entry
    python3 sim/simulator.py costs --help    the cost of making a good, from the solver's recipes
    python3 sim/simulator.py why <node>      one node's cost, broken down recursively
    python3 sim/constants.py --burndown      declared numbers, and the temporary heuristics still to derive

What the code does today, in one paragraph each:

- **Cost of making.** `sim/prices/` holds the solver (`solve_prices.py`) and the per-good calculator
  (`making_cost.py`, `cost_of_making`). Recipes (inputs, labour hours by trade, yield) are authored in
  `data/production/`. There is no price table; `data/prices.json` is deleted (`Complaints/closed/119`).
  The solver prices in unskilled labour-hours as the numeraire. Ore and land rent, capital and energy are inputs to
  it; where it falls short of the cost of making is the subject of the open complaints on prices and costs.
- **Market prices.** The default economy (`sim/economy/`, `ECONOMY_AGENTS.md`) clears every market each year; its
  cleared prices, not the solver's, are what agents pay. Making `sim/economy/` the one owner of prices and traded
  volumes, with the solver only a cost calculator, is `ONE_PRICE_OWNER_PLAN.md` (`Complaints/507`).
- **The wage.** It comes from the labour market in `sim/labour/market/`. Labour having one owner, and the
  engine-side staff books not meeting that market, are open under `Complaints/964`, `556` and `963`.
- **Food and people.** Agriculture and demography are wired through the engine's yearly demographic step
  (`WIRING_MILESTONE_4.md`).

The domain modules under `sim/world/` were each built and tested standalone first, then wired in. Which of them
the engine imports: `grep -rn "from sim.world import\|import sim.world" sim/engine`. A module that exists but is
imported by nothing is not part of the game.

## Order of work still open

1. Close `Complaints/964` (labour single owner, one national price rule, the legacy analytic price model).
2. `ONE_PRICE_OWNER_PLAN.md` stages left (`Complaints/507`).
3. Replace temporary heuristics, longest-lived first: `python3 sim/constants.py --burndown`.
4. The domains of Part 3 with no module yet: list the open ones with the status grep above.

**Scope.** Sixteen domains is a destination. Six of them, done properly, is a
year of work that produces a simulator that calculates its own costs. Starting
all sixteen produces sixteen stubs and no prices.
