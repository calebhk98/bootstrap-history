# One price owner: the agent economy

**Status:** partly built; the static book (stage 6) is deleted. Answers `Complaints/507-prices-and-traded-volumes-have-two-owners.md` (read its
`**Status:**` line for the live state). Owner decision: the agent economy (`sim/economy/`, reached through
`sim/markets/`) is the only owner of prices and traded volumes; the price solver (`sim/prices/`) becomes a
cost-of-making calculator. Sequel to `ONE_DEMAND_MODEL_PLAN.md` (one household demand kernel). What the price and labour re-audit left is in `Complaints/964`; read that complaint for it.

Rules this plan keeps (CLAUDE.md section 4): no hardcoded outcomes, no content ids in the engine, every
transitional shortcut labelled, no save migration. A stage changes behaviour on purpose, so the fingerprint proves
nothing here; each stage is proved by relationship tests (ranges and relationships, never dated values).

## What is built

Each item names where it lives now; confirm with the command before relying on it.

- **The solver is a cost calculator.** The demand model, clearing and glut handling are out of the solver. The
  calculator is `cost_of_making` (`sim/prices/making_cost.py`: inputs at the prices handed in, labour at the wages
  handed in, plant charge at the rate, rent as an argument, the cheapest technique a held set allows) and the
  long-run table `long_run_costs` (`sim/prices/long_run_costs.py`). Neither reads population, income or demand.
  `sim/prices/rent_standin.py` supplies a labelled stand-in for ore and land rent where the economy has none; a
  joint run's split uses a reference price when one is handed in, else the labelled fallbacks in
  `sim/prices/joint_allocation.py`. List them: `python3 sim/constants.py --kind temporary_heuristic | grep -i "UNPRICED\|STAND_IN"`.
- **The opening is seeded from the calculator.** `opening_costs` (`sim/markets/port_costs.py`) takes the opening
  prices from the long-run costs; a good a late technique allows is seeded by `late_goods_costs`
  (`sim/markets/port_late.py`). The opening income, runs and metal are `sim/economy/opening*.py`
  (`STATIONARY_OPENING.md`).
- **Prices to pay come from the economy.** `sim/economy/prices_at.py` (`prices_at`, `price_response`,
  `offered_units`) and the markets module's goods pricing (`sim/markets/goods_pricing.py`, `goods_offers.py`) give
  the price at the buyer's tile, carriage and the climb an order causes. The economy keeps the order books of the
  areas holding the capital and the playing seats' base tiles (`market_curves.kept_areas`).
- **Traded volumes come from the economy.** Real output is measured from the economy's `traded_volumes` against its
  opening basket (`sim/reporting/output.py`); the quote's available tonnes is the economy's offered quantity.
- **Cost comparers use the calculator at the economy's prices.** `CostBook` (`sim/prices/cost_books.py`,
  `entry_cost.py`) is a book over `cost_of_making` fed the economy's input prices, wages, rate and land rent; the
  node market factor is economy price over long-run cost (`sim/production/node_revenue_market.py`).
- **Unsold stock is searched within the year.** `sim/economy/unsold_search.py` (`clear_with_search`) lowers the asks
  of sellers left with unsold stock to the highest common level at which they sell out or reach their floor; the
  floor includes the queued holding value (`inventory.queued_holding_value`).

## What is not built

- **The solver still has readers that want a price.** List them:
  `grep -rn "solved_prices(\|_price_tables()\|_material_prices()" sim --include=*.py | grep -v tests`. Today these
  are the wage schedule's opening anchor (`sim/workforce/wage_schedule.py`), the energy price tables
  (`sim/prices/energy_prices.py`), and the markets module's table reads (`sim/markets/goods_offers.py`,
  `sim/markets/port.py` `_material_prices`). The cost table closes the recipe graph at runtime for them, so `ENGINE_SOLVE_TOLERANCE`
  and the interest-rate band (`sim/prices/prices.py`, `sim/engine/shipped_rate_bands.py`) stay until they move.
- **The static commodity book is gone.** `market_state` reads sold, unsold and unmet from the economy's record (`sim/markets/clearing.py`); the markets module keeps only the year's flows by party. Partner economies are inside the agent economy (`sim/content/foreign_economies.py`, `sim/markets/port_world_foreign.py`).
- **Trader cargo** still prices some home goods at the cost table with the economy's response as a factor
  (pricing them at the economy's port price made home-bound cargo stop after a year).
- **Farm effort** (`Complaints/513`): farm work is chosen inside the economy; the staple's price near satiation and the sale of surplus past it are open.
- **Three copies of cost arithmetic**: `sim/prices/solve_prices_core.py`, `sim/economy/unit_cost.py` and
  `sim/economy/notional.py` (`cheapest_cost`). Merging them into one `sim/world/` kernel changes no behaviour, so
  its proof is the fingerprint.
- **The settled-economy checks.** The opening still does not settle (`Complaints/473`, `526`, `607`, `608`,
  `960` to `963`); the relationship checks print with `python3 sim/simulator.py opening-checks` (minutes) and the
  yearly ones with `python3 sim/simulator.py economy-check`. The proofs this plan once named for price over making
  cost and for output per head after a population fall were deleted or red on an unsettled economy
  (`Complaints/558`, `Complaints/closed/523`); they come back when the economy settles.

Heuristics a stage deletes are counted by `python3 sim/constants.py --burndown` (this plan states no totals).

## Risks that still apply

- **Speed (`Complaints/497`).** Measure a year before and after a stage with `echo "step 5" | python3 sim/simulator.py
  play --session FILE`; a stage that makes a year slower says so in its commit.
- **Save and load (CLAUDE.md 4.6).** Stages change what is saved: drop fields, no shim, and keep the round trip
  (the save and load tests under `sim/tests/`, `--session` on every command).
- **Shipped openings.** A change to economy or engine source stales `openings/`; regenerate with
  `python3 sim/simulator.py openings --prune` before a PR.
- **Seeding from costs gives an opening where every price equals cost,** with no scarcity rent; the spin-up has to
  find the rest (`Complaints/473`), and if it cannot the fix is in the economy, not a seeded premium.
- **Joint products without anchors.** Without a reference price a co-product with no market may price oddly; the
  labelled fallback stays and `--burndown` counts it.
- **Baseline drift (CLAUDE.md 4.2).** Judge a stage on the ensemble's distributions
  (`python3 sim/simulator.py baseline-ensemble`, slow), not on dated events.
