# The opening sizes producers for food that households grow themselves in year one

**Status:** closed (the opening settles own-plot growing with income and hiring; see Resolution)

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

## Resolution

- `_settle_income` (`sim/economy/opening.py`) now iterates, inside each income pass, the hired hours the
  demand needs, the idle hours left of what each cohort offers, what those hours grow on its own plot
  (`households_own.own_production`, the economy's own options) and the floor bids cut by it
  (`households_own.less_what_it_grew`, the function the year also calls). `_final_demand` uses the settled
  grown units, so producers are sized to what is left to buy. `sim/economy/opening_own.py` holds the estimate.
- Stand-in: hired hours are placed on tiles by their share of final demand value, labelled
  `HIRING_FOLLOWS_DEMAND_SHARE` (retire: placing producers before settling income). Offered hours are the
  working people times the working hours; the year's workforce by trade does not exist before producers do.
- Scenarios that state `opening_income_per_head` bypass the fixed point and grow nothing at the opening (526).
- Tests: `sim/tests/test_opening_grows_its_own.py` (fixture with a land-only grain recipe). Self-grown share of
  the food floor, opening against the first year: fully self-fed 0.0 before, 1.0 after, year one 1.0; partly
  fed (few hours offered) 0.0 before, 0.8 after, year one 0.8. Command:
  `python3 -m unittest sim.tests.test_opening_grows_its_own`.
- Rome (`sim(civ="rome_100ad")`, measured with a throwaway script): the food floor is fully self-grown at
  the opening and in the first year (share 1.0 both). The settled income collapses: income per head falls
  from the ceiling to the demand of a market with no food floor and then geometrically toward zero (it was
  about 43 before; producers 5236 before, 2234 after, mostly tiny). That is the yearly model's own
  state once the idle hours grow every floor (the reviewer's figure above), now reached at the opening: with
  hiring decided by demand and idle hours going to the plot, the fixed point of income, hiring and growing
  has no positive market solution unless a floor needs something households cannot grow. The attractor is
  the cause to take up under 473 and 526 (hours go to a plot only when the wage is below the plot's worth).
- Not measured here: the shipped openings checks. Run `python3 sim/simulator.py openings`.
