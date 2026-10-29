# Module `materials`

Material supply and demand, the resource throttle, electricity, material reach and the materials a project consumes.

**Status:** moved (branch `mr/materials`). The package is `sim/materials/`; this file describes what shipped. Counts come from the
module spec (`python3 -c "import sys; sys.path.insert(0,'.'); from sim.materials.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies), len(s[0].reads))"`).

## What changed from the draft

- **Views:** about 40 instead of 6, one per question the readers ask (the draft's six bundled several old methods each). None is
  cached: the tonnes ledger, the projects and the market behind them are still written outside the owners' commands.
- **Commands:** `ApplyThrottle(node_id=None)`, `SettleProjectMaterials(node_id)` (moved from the projects module's needed commands),
  and three bookkeeping commands the engine sends: `ForgetReadings` (seat switch, handover, load), `RestoreReadings` (after a load),
  `CaptureReadings` (before a save). They keep the old timing of the remembered demand tables exactly: the saved field is written
  at save time for the acting seat only, and a seat switch forgets the tables.
- **`_peek_throttle` is gone.** `resource_throttle(node_id=None)` is a pure quote (pace, binding) worked out from the stock and the
  year's opening snapshot without touching them; `ApplyThrottle` takes the same reading (`rules.throttle_reading`) and banks it
  through the ledger's `BankStock`, the market's `ResetDraws`/`NoteDraw`, and counts the shortage. A repeat with nothing changed
  replays the reading. The replay signature carries the tonnes ledger's `writes` counter, which replaces the old
  `_stock_throttle_sig = None` reset inside `ChangeStock`.
- **The tonnes ledger's creation and sweep** moved to `sim/ledger/rules.py` (`StockLedger`, `settled_stock`, `year_opening_record`),
  run where the ledger's bridge view reads it, so the sweep happens on the same reads as before. The ledger gained `BankStock` and
  the view `goods_stock_opening` (the opening snapshot as the books stand, nothing recorded by asking).
- **Markets commands** `ResetDraws`, `NoteDraw`, `NotePurchase` exist in `sim/markets/` (commands only; the bridge applies them).
- **Dropped as dead:** `material_market_factor` (no caller). `wire_chain_report` stays an engine forwarder (it needs the engine's
  commodity catalogue).
- **Stays in the engine for the prices and markets modules:** `_commodity_ledger`, `_material_commodity_map`, `_done_memo`,
  `_producers_memo`, `_priced_key`, `_material_price_per_kg`, `material_trade_quote`, `buy_material_stock`, `sell_material_stock`,
  `material_purchase_cost` (`economy_materials.py`).
- **Moved with it:** `material_capacity.py` into `sim/materials/capacity.py`; `material_throttle.py`, `material_scarcity.py`,
  `project_throttle.py`, `shortage_conditions.py` into `rules.py`; `material_availability.py` into `availability.py`; the
  constants into `constants.py`.

## State owned

Seat: `shortages`, `throttle`, `binding`, `shortage_condition`, `material_demand_at_last_throttle` (were `holdings/<same>`;
relocations in `sim/tests/equiv_fields.py`). A handover carries the slot and refuses a replacement that holds one.

## Debts

Reads through the bridge (`sim/engine/bridge_materials.py`): `legacy_projects`, `hard_prerequisites`,
`shared_bill`, the market views `partner_import`, `can_be_bought`, `purchase_quote`, `agent_producer_capacity`,
and the price and catalogue views. Forwarders left on `Sim` (`sim/engine/forward_materials.py`): `_material_tag`,
`material_shortfall_t`, `_society_output_tonnes`, `_material_market_tonnes`, `_own_material_supply`, `_own_production_tags`,
`_demand_by_supply_tag`, `demand_and_own_supply_by_material`, `MATERIAL_CHECKS`, `annual_material_demand`, `material_price_factor`,
`material_market_summary`, `material_unsupplied_sentence`, `materials_report`, `wire_chain_report`, `_material_stock`,
`material_stock_t`, `peek_resource_throttle`, `peek_project_resource_throttle`, `generation_breakdown_kw`,
`installed_generation_kw_by_tier`, `_electricity_demand_kw`, `project_material_needs`, `project_material_bill`,
`project_material_parts`, `project_cost_without_materials`, `failure_loss`, `bounty_price`.
