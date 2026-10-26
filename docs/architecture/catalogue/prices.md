# Module `prices`

The calculator-backed price tables, the cost books producers offer from, the commodity catalogue, and the memos keyed on what
is built and run. The solver (the cost-of-making calculator) lives here whole.

**Status:** moved (branch `mr/prices`). The package is `sim/prices/`; this file describes what shipped. Count the surface with
`python3 -c "import sys; sys.path.insert(0,'.'); from sim.prices.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].reads))"`.

## What changed from the draft

- **Views:** one per question the readers ask, not the draft's four. `material_prices` (the table), `material_price` (keyed by a
  material key or a curated commodity), `price_tables` (labour-hour prices and their provenance, the solver's own table),
  `material_price_basis` (with the import override), `price_index`, `commodity_record`, `material_commodity_map`,
  `commodity_country_output`, `commodity_floor_ratio`, `concern_offers`, and the two memos `done_memo` and `producers_memo`
  (quotes that take the function to remember). None is cached: the techniques, projects and economy behind them are written
  outside any command of their owners.
- **`cost_ratios` split:** `entry_cost_ratio`, `concern_cost_ratio` and `materials_of_commodity` have no reader outside the module
  (only `concern_offers` uses them), so they are methods, not views. The floor is its own keyed view because the clearing reads it.
- **`price_index`** is the civilisation's capital price level; nobody else claimed it, and it is read by agriculture, resources
  and hazards. `Sim.price_index` stays as the attribute the engine code uses, set from the same field.
- **No commands, no saved state:** the module owns derived values and caches only, so there are no relocations.
- **The re-entry guard** (`_reading_market_rate`) is the module's private field. Asking the market for its rate may need these
  prices, which ask for the rate again; while the first ask is open the starting rate answers. The behaviour is the old one:
  the flag is set before the rate is asked and cleared in a `finally`, and the chain still runs through one module instance
  (`market_rate` bridge, the `_material_prices` forwarder, the `material_prices` view, `price_tables`, `banded_market_rate`).
- **Files moved from `sim/engine/` to `sim/prices/`:** the four `solve_prices*` files, `prices.py`, `making_cost.py`,
  `long_run_costs.py`, `rent_standin.py`, `entry_cost.py`, `energy_prices.py`, `price_change.py`, `disposal_cost.py`,
  `joint_allocation.py`, `identity_cache.py`, `commodities.py` (the catalogue), `solve_cache.py`. `capital_builds.py` (pure, used by
  the tree loader too) went to `sim/world/`. `economy_cost_book.py` became `CostBooks.economy_cost_book` over views.
  `IncumbentPricesMixin` became `tables.py`, `ProducerCostsMixin` became `cost_books.py`, the price parts of `economy_materials.py`
  became `memos.py`; `rules.py` holds the plain rules.

## Debts

- **`sim/prices/engine_seam.py`** is the one file that imports `sim.engine`, each service where it is called: the production and
  tree loaders, the civilisation loader, the calculated-goods wrapper, the shipped openings and the source closure. The solver
  needs the production catalogue and the civilisation files before any game exists, and those loaders have no owner yet.
- Reads through the bridge (`sim/engine/bridge_prices.py`): `farm_land_hectares`, `material_seller`, `agent_wage`,
  `agent_land_rent`, `concern_baskets_now`, `venture_ramp`; plus `techniques_in_use`, `price_epoch`, `producers_stamp`,
  `household_prices`, `market_rate`, `hour_wage`, `money_per_labour_hour`, `is_venture`, `operating`, `legacy_projects`.
- `rules.HOME_SELLER` repeats the goods market's id for the home seller until markets publishes a view that says it.
- Forwarders left on `Sim` (`sim/engine/forward_prices.py`): `_material_prices`, `_price_tables`, `_material_price_per_kg`,
  `_priced_key`, `material_price_basis`, `_commodity_ledger`, `_material_commodity_map`, `_done_memo`, `_producers_memo`,
  `commodity_floor_ratio`, `founder_concern_offers`.

## Hard spots, and how they were handled

- **The solver stays whole.** It is a pure function of its inputs; its callers (the tree loader, the economy port, the node
  rederivation) reach it through `sim.prices.api` as before. Nothing of its arithmetic or iteration order changed.
- **The spin-up cache key** hashes the source the spin-up can import, found by reading imports. The module's own code is not
  imported by the engine (the assembly finds it by file), so `api.py` names `Prices`, which keeps `module.py` and its rules in
  the closure. File paths are part of the digest, so moving the files changes the key once; the second build after the move hits.
- **The four hand caches** (`_incumbent_table_cache`, `_price_tables_cache`, `_material_prices_cache`, `_cost_book_cache`) are
  module fields with the same stamps (identity of the granted set and the techniques in use, banded farmland and rate). They fold
  into one version per view when production and markets move and the views can be cached.
- **The prices <-> production cycle** (`price_epoch`) is untouched: techniques change at project completion, not within the year.
- **Direction:** `ONE_PRICE_OWNER_PLAN.md` moves market prices to the agent economy and leaves this module the cost calculator;
  none of that behaviour changed in the move.
