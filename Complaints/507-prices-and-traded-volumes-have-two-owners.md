# Prices and traded volumes have two owners: the engine's price solver and the agent economy

**Status:** partly - owner decision (2026-10-14): the agent economy is the only owner of prices and volumes; the solver is a cost-of-making calculator only. The static commodity book, `world.market`, its stock and the partner books are gone, and a market's report (`Clearing.market_state`, `GoodsMarket.state`) is the economy's record. What is open is the solver's remaining readers of its price tables (below)

The solver (`sim/prices/prices.py` `solved_prices`, `sim/prices/solve_prices*.py`) has no demand model or clearing. The
plan and its built stages are in `docs/architecture/ONE_PRICE_OWNER_PLAN.md`.

## What is left

Readers that still want a solver price; list them with
`grep -rn "solved_prices(\|_price_tables()\|_material_prices()" sim --include=*.py | grep -v tests`:

- the wage schedule's opening anchor (`sim/workforce/wage_schedule.py`);
- the energy price tables (`sim/prices/energy_prices.py`).

The markets module's table reads (`sim/markets/goods_offers.py`, `sim/markets/port.py`) are gone: the grep no longer finds them there.

What it would take: each reads the economy's price (`sim.economy.api`, `sim/economy/prices_at.py`) and the solver keeps one
job, the cost of making a good with given techniques and input prices. A fix on one side of the seam is invisible on the
other, so agents patch symptoms with labelled constants (509). 478, 502 and probably 473 sit on this seam.

`price_over_making_cost_band_validation` was deleted in the rule-test pass: it read the unsettled economy and could not name
a function. The relationship, on the full-length opening, is `python3 sim/simulator.py opening-checks` (the "prices over
making cost" row).
