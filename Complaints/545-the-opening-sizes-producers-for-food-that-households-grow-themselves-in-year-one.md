# The opening sizes producers for food that households grow themselves in year one

**Status:** open

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
