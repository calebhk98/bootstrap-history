# Prices and traded volumes have two owners: the engine's price solver and the agent economy

**Status:** open - owner decision (2026-10-14): the agent economy is the only owner of prices and volumes; the solver becomes a cost-of-making calculator only; stage 1 of `docs/architecture/ONE_PRICE_OWNER_PLAN.md` is built (the solver has no demand model), stages 2 to 8 are open

Closed 115 made the agent economy the only economy, but the engine still runs a second equilibrium model of
its own. `prices.solved_prices` (`sim/engine/prices.py`, `solve_prices*.py`) builds a demand model
(`need_demand.NeedDemandModel`, through `joint_allocation.build_demand_anchors` and `market_demand.py`) and
clears it (`clearing_with_glut`). Project costs, the wage schedule (`wage_schedule.py`), producer costs
(`producer_costs.py`), the price basis (`incumbent_prices.py`) and the market factor on node output all
read that solve. The agent economy clears real markets each year and gives the same goods a second price
and a second traded volume.

The two are joined by bridges, each a place the models can disagree:

- `price_ratio` / `market_price_ratio`: the spot price over the solver's long-run cost.
- `goods_price_over_wage`: carries the solver's tables to the economy's price level.
- `notional.thin_market_prices`: blends a thin market's price back toward the solver's making cost (502).
- `RealOutputMixin._follow_cleared_volumes`: the engine's traded tonnes follow the economy's cleared volume
  for goods a late recipe makes (478); every other good still reads the opening reference, because wiring
  them all swung output per head by a large factor (the two models disagree on volumes).

Why it matters: a fix on one side of the seam is invisible on the other, so agents patch symptoms with
labelled constants (see 509). 478, 502 and probably 473 sit on this seam.

What it would take: one price and one volume per good and area, owned by the agent economy. The solver
keeps one job, the cost of making a good with given techniques and input prices (no demand model, no
clearing), used for entry decisions, quotes and the opening's seed prices. Every reader listed above moves
to the economy's prices through `sim.economy.api`. Measure progress with
`grep -rn "solved_prices(\|_price_tables()" sim --include=*.py | grep -v tests`.

## Report path (outside review)

`GoodsMarket` (`sim/engine/goods_market_api.py`) quotes from the agent economy, but `GoodsMarket.state`
returns `Sim.market_state` (`sim/engine/market_clearing.py`), computed from the older `world.market`
model and its `market_book` capacity and stock, and `GoodsMarket.add_stock` writes to that older stock.
So one interface reports a different market from the one it trades in. Reports should be derived from
the same clearing and settlement results as transactions; the cost-of-making answer stays, named as a
cost estimate. This is the reviewer's suggested first slice of the migration: small and contained.
