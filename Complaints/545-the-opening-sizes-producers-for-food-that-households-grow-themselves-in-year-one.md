# The opening sizes producers for food that households grow themselves in year one

**Status:** partly - the plot fixture's year-one runs match the opening's sizing (473 Update 8); Rome not re-measured (needs a spin-up-trace read)

Found by an outside reviewer reading the repository, checked against the code.

## What happens

- The opening (`sim/economy/opening.py`) sizes production capacity from what households buy. It has no
  notion of households working their own plots: no reference to growing or own plots in that file.
- In every year, `Economy._grow_own` (`sim/economy/economy.py`) lets household labour that nobody hired
  grow necessities on the household's own land, and `_less_what_it_grew` (`sim/economy/year_goods.py`)
  cuts each floor bid by the share of that need's floor the household grew.
- So the first year removes much of the demand the opening built firms for. The reviewer measured Rome's
  first year with the food floor fully self-grown and household goods budgets cut by almost all of
  their opening value; recorded cash income per head falls by a similar share. That figure is the
  reviewer's and was not re-run here. Cash income excludes food grown at home, so the fall is in market
  demand, not in living standards.

## Why it matters

Firms built for buyers who disappear lose sales, lay off, and the wage and price level fall for years.
This is one candidate cause of the spin-up never settling (473); the opening and the yearly model
describe different economies.

## What it would take

- Self-production solved in the opening jointly with employment, land and purchases: a household's
  hours split between its plot and the labour market at the opening wage, and firms sized to what is
  left to buy.
- A test: at the opening, the self-grown share of each need and the market demand for it are the
  values the first simulated year produces, within a stated tolerance, under no shock.
- Related: 526 (the opening income fixed point has no investment, so it opens at subsistence), 513.

## Tried and failed (code not kept)

An attempt (commit `6bfa0b32` on a branch named `opening-sizes-producers-net-of-own-grown-food`) ran the year's own-plot rule inside the
opening's fixed point (a module `opening_own.py`, reusing `households_own.own_production` and `year_goods._less_what_it_grew`), so
the opening's grain demand matched what year one grows. The branch is deleted and the commit is not in this repository, so the code
cannot be recovered; `sim/economy/opening_own.py` does not exist. It passed the quick tier but broke the slow topic
`agent_economy_wiring` on Rome: after the opening, households offered no savings at all (`record.funds_offered` zero, so
`economy_api.credit_room` is None). That is the collapse recorded in 526: with the food floor grown at home, the saving leak drives
the settled income toward zero. So the work lands together with 526 (607), with `agent_economy_wiring` and
`full_length_opening_checks` green. Reproduce the symptom on any rebuilt attempt: (the test was removed from the suite).

## Update: the fixture now has plots

`economy_fixture.stationary_setup` gives the farm recipe a `land_per_run`, so households grow part of their own grain in
the fixture and the own-plot cut can be reproduced there (previously not reproducible: 473 Update 6). The opening still
sizes producers for the whole food demand; sizing net of the plot is not done.

## Update: on the plot fixture the year-one sales equal the runs the opening sized (473 Update 8)

On `economy_fixture.small_setup(land_per_run=...)` (households grow part of their food from year one) the farms' year-one runs
are within one per cent of the runs the opening sized and the grain bought equals what they produce, so the first-year shortfall
this complaint describes does not appear on the fixture (the opening's demand is already net of the households' own-plot plan).
Rome is not re-measured; the claim stays open until `spin-up-trace` is read for it.
