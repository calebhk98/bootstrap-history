# The opening sizes producers for food that households grow themselves in year one

**Status:** partly - the opening now sizes producers for what households buy after their own plots (Update 9); the year-one purchases still fall well short of the opening's final demand for a reason that is not the plot (Update 9); Rome's opening did not finish in five minutes, so Rome is not re-measured

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

## Update 9: the opening runs the year's own-plot rule (opening_own.py)

- The fault was in `opening.py` `_opening_bids`: the bids stopped at `households.goods_orders`, so every floor was sized as bought.
  `opening_own.OwnPlots` now applies the two functions of the year: `households_own.own_production` on the hours a cohort has left (its
  working hours less the share producers hire and the household work it does itself) and `year_goods.less_what_it_grew` on the bids.
  The share producers hire follows from the runs the net demand takes, so `_settle_income` settles it at each income: the least share the
  demand agrees with (a start from the whole-hours share is a second, worse fixed point where nobody grows anything).
- The root find of the income saves-nothing condition has no solution once floors are cut (the cut frees budget that is saved at every
  income; the collapse recorded in 526). The budget the cut frees is therefore counted as spending in kind (`OwnPlots.in_kind`), not as
  saving, so the opening income still includes the food grown at home. Cash income in year one is below it; that is 526, not fixed here.
- The muscle-power over-sizing came from a joint recipe: the pig-feeding run (lard) takes bran, bran is made only alongside flour, and
  the input-output solve ran the mills for the bran (runs = the larger of what each output needs), dumping flour nobody buys, and the
  muscle that mills it. `opening_runs.required_runs` now holds the users of a by-product to what the runs for its makers' main outputs
  make (`by_product_ceilings`); the lard falls short instead and the opening basket records the shortfall.
- Norse (`spin-up-trace --civ norse_900ad --years 3`), hired hours by year: before 4.98e8, 3.02e8, 5.57e7; after 6.02e7, 4.08e7, 7.8e6.
  Planned revenue of the producers (expected sales at opening prices) against year-one receipts: before 3.4e9 against about 1.1e8;
  after 2.9e8 against 1.5e7. Year-one volumes of the final goods are still only about a tenth of the opening's final demand for every good,
  grown-at-home or not: that gap is not the own plot and is open.
