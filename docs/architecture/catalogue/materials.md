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

## Width review

Task: "A width review for each module that depends on more than 15 others" (`MODULE_MIGRATION_TASKS.md`, Phase 6b). Width is measured with `python3 tools/measure/module_graph.py --modules` (declared reads of other modules' views, declared sends of their commands, modules those reach). Before this review: reads 56, sends 7, modules depended on 18. After the commits of branch `mr/width-markets-land-materials`: reads 54, sends 7, modules depended on 17 (foreign_trade is gone). The per-file groupings below have no committed command: they come from grepping `needs.<view>` in each file of `sim/materials/`, so re-measure before acting on one.

### What it depends on, by what it asks

| Owner | Reads and sends | What materials asks of it | Used in |
|---|---|---|---|
| projects | `active_projects`, `active_project_ids`, `active_projects_version`, `project_cost`, `project_cost_now`, `opposition_factor`, `cost_money_factor`, `rebuild_work_factor`, `failure_reset_share` | The projects drawing material, and the multipliers on a project's cost. | `demand.py`, `throttle.py`, `electricity.py` (the projects); `project_bill.py` (the cost factors) |
| markets | `goods_quote`, `can_be_bought`, `purchase_quote`, `partner_import_tonnes`, `agent_producer_capacity`, `producers_stamp`; sends `ResetDraws`, `NoteDraw`, `NotePurchase` | Who sells a material, at what price and how much a partner brings; what the economy's producers make. | `supply.py`, `availability.py`, `project_bill.py` |
| resources | `empire_output`, `mine_capacity`, `mine_depletion`, `forest_hectares`, `nitre_beds`, `found_deposits`, `mine_works_materials`, `shortage_remedy_plan` | What the seat's own workings, woodland and beds yield, and what to say about a shortage. | `supply.py`, `throttle.py` |
| knowledge | `tree_nodes`, `techniques_held`, `techniques_version`, `visibility`, `hard_prerequisites` | The tree and what is held and known. | everywhere |
| ledger | `goods_stock`, `held_goods`, `goods_stock_opening`; sends `BankStock`, `ChangeStock`, `PayEdge` | The tonnes held and every movement of them. | `supply.py`, `throttle.py`, `project_bill.py` |
| prices | `material_prices`, `material_commodity_map`, `commodity_record`, `commodity_country_output` | The price table, the commodity each material is filed under, the national output. | `supply.py` |
| land | `tiles_listed_by`, `forest_increment`, `mineral_scale`, `material_cost_factor` | The territory's woodland growth and mineral scale; the distance factor on materials. | `supply.py`, `project_bill.py` |
| production | `running`, `running_stamp`, `price_epoch` | Which concerns run, and a stamp for the memo. | `supply.py`, `throttle.py`, `project_bill.py` |
| core, demography, mechanics | `year`, `civilisation`; `default_population`, `pop_scale`; `mechanic`, `effect_best` | The clock, the country's file, the headcount scale and the mechanics' numbers. | `supply.py`, `module.py` |
| finance, ventures, freight, sharing, diffusion | `can_pay`, `purchase_refusal`; `operating`; `material_freight_factor`; `shared_bill`; `civ_cost_factor` | One fact each. | `project_bill.py` (finance, sharing, diffusion), `supply.py` (ventures, freight) |
| reporting | sends `RecordEvent` | The shortage notes. | `throttle.py` |

### Findings

**(a) Views that mirror one method of an owner.**

- Merged: `partner_import` (markets) answered a pair, seller and tonnes, and materials made tonnes of it with a second read of foreign_trade's `foreign_supply_tonnes` (`supply.py`, `import_tonnes`). Markets now publishes `partner_import_tonnes`, the one number materials asks, and materials no longer reads foreign_trade. The rule that an unlimited route brings nothing is a plain function in markets, `import_tonnes_to_home` (`sim/markets/goods_imports.py`), tested by `test_import_tonnes_to_home`. The old fallback to the partner's own supply never applied: a route is unlimited only when the partner's supply is itself unlimited, which the fallback then also read as unlimited and turned into zero.
- Merged: `tree[node_id]` (knowledge's keyed view) was read once, in the shortage note, for a node's name; `tree_nodes()[node_id]` answers it, and `tree` is no longer read. A test, `test_shortage_note_names_slowed_projects`, was added, because the shortage note had no test of its names.
- Proposal, projects (under another review): materials computes `project_cost_without_materials` as the tree's labour and capital cost times `cost_money_factor`, `civ_cost_factor` and `rebuild_work_factor`, and prices the materials part with `opposition_factor` and land's `material_cost_factor`. That is five factor views from three owners to answer one question, "the multipliers on a project's cost". A projects view `project_cost_factors(node_id)` would replace five reads (and diffusion's `civ_cost_factor` stops being a dependency of materials). `project_cost` and `project_cost_now` are the same question again (the frozen bill, or what starting today costs).
- Proposal, projects: `active_projects`, `active_project_ids` and `active_projects_version` mirror one table three ways (`demand.py` keys its memo on the version and iterates the ids). One view returning the active projects with their change stamp would be one read.
- Proposal, production: `running` and `running_stamp` (production) are the same table and its stamp.

**(b) A sub-domain that reads its own owners.**

- **The project bill** (`project_bill.py`, 126 lines; the views `project_material_needs`, `project_material_bill`, `project_material_parts`, `project_cost_without_materials`, `own_output_claim`, `bounty_price`, `material_upfront_refusal`, `failure_bill`, `failure_loss`; the command `SettleProjectMaterials`). It is the only file that reads finance, sharing, diffusion, `project_cost`, `project_cost_now`, `opposition_factor`, `cost_money_factor`, `rebuild_work_factor`, `failure_reset_share`, `material_cost_factor` and `purchase_quote`: twelve of its fifteen reads are read nowhere else in the module. It prices and pays what a project needs, which is a project's cost, not the material economy. Proposal, not built: move it into projects (or a module `project_bill`). It needs from materials the own-supply claim (`unclaimed_own_supply`, in `supply.py`), which would become a materials view; the commands it sends (`PayEdge`, `NotePurchase`, `ChangeStock`) go with it. Materials would stop depending on finance, sharing and diffusion and keep three of the nine projects reads (the active projects, their ids and version).
- **Electricity** (`electricity.py`; the views `generation`, `generation_breakdown`, `generation_by_tier`, `electricity_demand`). It reads the active projects, `hard_prerequisites`, `techniques_held`, `operating`, `mechanic` and `tree`, all of which materials reads for other reasons, so moving it would not narrow materials. It is power, not material; a module `power` is a reasonable name if the module ever needs a purpose-built owner, but it is not a width fix.

**(c) Pass-through dependencies.**

- `cost_money_factor` (projects) is `price_index` (prices) as a float (`sim/projects/costs.py`). Materials could read `price_index` directly and drop one projects read, at the cost of touching four test fakes and of reading around the projects module's own name for the question. Not done: the projects review should decide whether the five cost factors become one view, which removes it anyway.
- `mine_works_materials` (resources) is `deposit_catalogue()["works_priced_materials"]` (land's catalogue, forwarded by `sim/resources/costs.py`). Reading land's catalogue instead would swap a resources edge for a land edge the module already has and spell the dictionary key in a second place. Left; if resources and land merge the catalogue question this goes with it.
- `material_commodity_map` (prices) is read with `material_pool` (materials' own view) to tag a material; nothing is forwarded.

### Why each remaining edge is needed

Materials is the ledger of what a seat can get and what a project needs. Supply is the sum of what the seat makes (resources, land, production, mechanics), what it can buy (markets, prices, freight) and what is held (ledger); demand is what the projects and concerns draw (projects, knowledge, ventures, production); the bill is the project's price (projects, finance, sharing, diffusion) and its payment (ledger sends). The cycle with markets is economic: materials reads quotes and sends `NoteDraw`, `NotePurchase` and `ResetDraws` so markets sees the draws; markets reads materials' tags, pool and output to file a trade under a commodity.
