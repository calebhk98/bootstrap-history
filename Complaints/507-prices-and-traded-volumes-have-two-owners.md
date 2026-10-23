# Prices and traded volumes have two owners: the engine's price solver and the agent economy

**Status:** partly - owner decision (2026-10-14): the agent economy is the only owner of prices and volumes; the solver becomes a cost-of-making calculator only. Stages 1 to 3 are built and 4 and 5 partly (the plan's status line, `docs/architecture/ONE_PRICE_OWNER_PLAN.md`, is the live record); the rest and the report path below are open

Closed 115 made the agent economy the only economy. The engine's solver (`prices.solved_prices`, `sim/engine/prices.py`,
`solve_prices*.py`) no longer has a demand model or clearing (stage 1), but project costs, the wage schedule
(`wage_schedule.py`), producer costs (`producer_costs.py`), the price basis (`incumbent_prices.py`) and the market
factor on node output still read its tables, while the agent economy clears real markets each year. Which readers
still do is in the plan's section 1.1 and the measure below.

Bridges that remain, each a place the two can disagree (check each still exists with grep before acting):

- `price_ratio` / `market_price_ratio`: the spot price over the solver's long-run cost.
- `goods_price_over_wage`: carries the solver's tables to the economy's price level.
- `notional.thin_market_prices`: blends a thin market's price back toward the solver's making cost (502).
- The engine's traded volumes follow the economy's cleared volumes (stage 4, partly built; the old
  `RealOutputMixin._follow_cleared_volumes` is removed, `sim/tests/test_real_output.py` asserts it).

Why it matters: a fix on one side of the seam is invisible on the other, so agents patch symptoms with
labelled constants (see 509). 478, 502 and probably 473 sit on this seam.

What it would take: one price and one volume per good and area, owned by the agent economy. The solver
keeps one job, the cost of making a good with given techniques and input prices (no demand model, no
clearing), used for entry decisions, quotes and the opening's seed prices. Every reader listed above moves
to the economy's prices through `sim.economy.api`. Measure progress with
`grep -rn "solved_prices(\|_price_tables()" sim --include=*.py | grep -v tests`.

## Report path (outside review)

`GoodsMarket` (`sim/engine/goods_market_api.py`) quotes from the agent economy, but `GoodsMarket.state`
returns `Sim.market_state` (`sim/engine/market_clearing.py`; `goods_market_api.py`, method `state`), computed from the older `world.market`
model and its `market_book` capacity and stock, and `GoodsMarket.add_stock` writes to that older stock.
So one interface reports a different market from the one it trades in. Reports should be derived from
the same clearing and settlement results as transactions; the cost-of-making answer stays, named as a
cost estimate. This is the reviewer's suggested first slice of the migration: small and contained.

`price_over_making_cost_band_validation` (the typical traded good sells at no less than its making cost and no more than a factor of three over it, half within the band, after four market years of an opened Rome) was deleted in the rule-test pass: it read the unsettled economy and could not name a function. The same relationship, on the full-length opening, is `python3 sim/simulator.py opening-checks` (the "prices over making cost" row).
