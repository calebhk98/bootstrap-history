# Module `materials`

Material supply and demand, the resource throttle, electricity and the materials a project consumes.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 6 / 1 |
| Old methods and properties owned (after regrouping) | 63 |
| Of those, referenced from another module's mixin code | 23 (9 classed read-only or pure by Appendix B, 14 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 35 (23 from mixins, 12 only from outside) |
| Views per used name | 0.17 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 6 |
| Views of other modules it reads | 21, from 12 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 1 |

**Existing surface and files.** Engine only: `MaterialSupplyMixin` (33 methods), `MaterialReachMixin`, `ElectricityMixin`, the demand half of `FreightMixin`, `ProjectMaterialsMixin`; function modules `material_throttle.py`, `material_availability.py`, `material_capacity.py`, `material_units.py`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `MaterialSupplyMixin` | `sim/engine/economy_materials.py` | 20 | 9 |
| `MaterialReachMixin` | `sim/engine/material_reach.py` | 4 | 1 |
| `ElectricityMixin` | `sim/engine/economy_electricity.py` | 13 | 5 |
| `FreightMixin` | `sim/engine/economy_freight.py` | 7 | 0 |
| `ProjectMaterialsMixin` | `sim/engine/project_materials.py` | 15 | 8 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 8 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `ELECTRICAL_PROCESSES`, `_ELECTRICITY_GATE_TOKENS`, `_cached_demand_by_tag`, `_cached_material_demand`, `_compute_material_bill`, `_demand_by_emp_key`, `_electricity_load_node_ids`, `_generic_market_share`, `_generic_market_share_uncached`, `_generic_national_output_t_per_yr`, `_generic_national_output_uncached`, `_makers_of`, `_material_demand_cache`, `_material_import_tonnes`, `_node_annual_tonnes`, `_output_scale`, `_peek_throttle`, `_standing_material_terms`, `_throttle_demand_split`, `_unclaimed_own_supply`, `_up_front_materials_money`, `buy_project_materials`, `chosen_fuel`, `failure_bill`, `material_market_factor`, `material_supply_route`, `shortages`, `wire_chain_report`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `MaterialsSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.holdings.binding` | seat | projects 23, <ui> 5 | - |
| `state.holdings.material_demand_at_last_throttle` | seat | core 1 | <engine-functions> 1 |
| `state.holdings.shortage_condition` | seat | <engine-functions> 2 | <engine-functions> 2 |
| `state.holdings.shortages` | seat | - | - |
| `state.holdings.throttle` | seat | <ui> 5 | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `material_pool` | keyed | no | Which commodity and supply-pool tag a raw material key draws on (static data). | `_material_tag`, `_normalize_material_name` | - | - | - | 12 |
| `material_demand` | table | yes | Annual tonnes demanded by material key and by pool tag, split lab-scale and industrial. | `annual_material_demand`, `_demand_by_supply_tag`, `demand_and_own_supply_by_material`, `CHARCOAL_PER_HA` | `holdings.material_demand_at_last_throttle` | `knowledge.techniques_held`, `production.running`, `demography.population` | `demand` | 5 |
| `material_supply` | keyed | yes | Tonnes the society, the nation, the market and the seat itself supply of a material; the market summary and price factors. | `material_market_summary`, `material_price_factor`, `material_market_factor`, `_own_production_tags`, `_national_output_tonnes`, `_society_output_tonnes`, `_material_market_tonnes`, `_own_material_supply` | - | `markets.others_trade`, `resources.mine_output`, `production.running` | `supply` | 7 |
| `resource_throttle` | quote | yes | The material pace of the portfolio or of one project, and the pool that binds it. Pure: no stock is banked. | `resource_throttle`, `project_resource_throttle`, `peek_resource_throttle`, `peek_project_resource_throttle`, `_peek_throttle`, `materials_report` | `holdings.shortages`, `holdings.throttle`, `holdings.binding`, `holdings.shortage_condition` | `ledger.goods_stock`, `material_supply`, `material_demand` | `stock`, `demand` | 6 |
| `project_materials` | quote | yes | What a project needs, what its own output covers, its bill and what a failure would cost. | `project_material_needs`, `project_material_parts`, `project_cost_without_materials`, `project_own_output_claim`, `project_material_bill`, `material_purchase_cost`, `bounty_price`, `failure_loss`, `project_material_upfront_refusal`, `material_unsupplied_sentence` | - | `material_supply`, `prices.material_prices`, `markets.trade_quote` | `demand` | 5 |
| `generation` | table | yes | Installed electrical generation in kW by tier, its breakdown and capacity. | `_electricity_demand_kw`, `generation_breakdown_kw`, `generation_capacity_kw`, `installed_generation_kw_by_tier` | - | `production.running` | `power` | 4 |

**Coverage.** 23 methods are referenced from other modules' mixin code: 22 are replaced by a view here, 1 by a command. 12 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 35 used names, 33 are covered by a view or command through the method itself, 2 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_peek_throttle`, `bounty_price`, `failure_loss`, `material_unsupplied_sentence`, `materials_report`, `peek_project_resource_throttle`, `peek_resource_throttle`, `project_material_bill`, `project_material_parts`, `project_material_upfront_refusal`, `project_own_output_claim`, `project_resource_throttle`, `resource_throttle`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `ApplyThrottle` | seat, scope (portfolio or project) | The writing half of `resource_throttle`: banks own output and prior stock, counts shortage, notes draws. Methods: `settle_project_materials`, `buy_project_materials` | `sim/engine/economy_electricity.py:431-533` | none: always applies | `holdings.shortages`, `holdings.throttle`, `holdings.binding`, `holdings.shortage_condition`, `holdings.material_demand_at_last_throttle` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `holdings.material_demand_at_last_throttle`: 1 site: `sim/engine/saveload.py:41`
- `holdings.shortage_condition`: 2 sites: `sim/engine/shortage_conditions.py:46`, `sim/engine/shortage_conditions.py:33`
- `holdings.shortages`: 1 site: `sim/agents/household.py:391`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `demography`: `demography.population` (input of materials.material_demand, pop_scale)
- `diffusion`: `diffusion.diffusion_index` (civ_cost_factor)
- `foreign_trade`: `foreign_trade.foreign_supply` (foreign_supply_tonnes)
- `knowledge`: `knowledge.techniques_held` (done_in_order, input of materials.material_demand, projects.done); `knowledge.visibility` (is_visible)
- `land`: `land.tile_facts` (geography, geography.material_cost_factor, world_map)
- `ledger`: `ledger.goods_stock` (_material_stock, input of materials.resource_throttle, material_stock_t); `ledger.goods_stock_opening` (_material_opening_stock)
- `markets`: `markets.others_trade` (input of materials.material_supply); `markets.trade_quote` (goods_market, goods_market.can_be_bought, goods_market.quote_buy, input of materials.project_materials)
- `mechanics`: `mechanics.effect` (effect_best); `mechanics.mechanic` (mechanic, nodes_with_mechanic)
- `prices`: `prices.material_prices` (_material_prices, input of materials.project_materials)
- `production`: `production.running` (input of materials.generation, input of materials.material_demand, input of materials.material_supply, running)
- `projects`: `projects.active_projects` (projects.active); `projects.project_cost` (cost_money_factor, opposition_factor, project_cost, project_cost_now); `projects.rebuild` (rebuild_work_factor)
- `resources`: `resources.deposits` (found_deposits, geography.mineral_scale); `resources.forest_and_nitre` (holdings.forest_ha, holdings.nitre_bed_m2); `resources.mine_cost` (MINE_OPEX_MATERIALS); `resources.mine_output` (_running_kept, input of materials.material_supply, mine_capacity, mine_depletion_factor)

Sends (commands of other modules):

- `markets`: `NoteDraw`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `seat_work`: `_step_materials` (`core_step_phases.py:125-139`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 32 | `throttle`, `binding`, `generation_breakdown_kw`, `bounty_price`, `failure_loss`, `project_material_bill`, `material_market_summary`, `annual_material_demand` |
| engine/(function modules) | 8 | `_material_tag`, `_material_market_tonnes`, `peek_project_resource_throttle` |
| engine/ui* | 6 | `_own_production_tags`, `_own_material_supply`, `_demand_by_supply_tag`, `_material_market_tonnes`, `_material_tag`, `_electricity_demand_kw` |
| engine/agents_port* | 1 | `_material_tag` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: 31 reads (`throttle`, `binding`, `generation_breakdown_kw`, `bounty_price`, `failure_loss`, `project_material_bill`, `material_market_summary`, `annual_material_demand`, `materials_report`); `engine/ui*` uses `_own_production_tags`, `_own_material_supply`, `_demand_by_supply_tag`, `_material_market_tonnes`, `_electricity_demand_kw` (private names reached from the UI).

## (h) Hard spots and caches

- `resource_throttle` reads and writes in one call (banks stock, notes draws, counts shortages) and screens ask it through `_peek_throttle`, a snapshot-and-restore (`economy_electricity.py:523-541`). Split into a pure quote and a commit command; the commit must repeat the same arithmetic, so share one function and test that quote then commit agree.
- The memo is keyed by a hand-built stamp including stock contents (`_stock_throttle_sig`); it becomes `goods_stock` + `material_demand` versions.
- Material demand sums floats over the done set; the order rule (CLAUDE.md section 5) holds only because `done_in_order` sorts. The knowledge view must keep that order.
- The `economy.capacity_pool` write in `_material_stock` crosses into foreign_trade/ledger fields; see ledger hard spots.
- Private names reach the UI through `ui_port`; each needs a public view or the screen goes.

Caches and version counters held today (feed for task 1.2):

- `_annual_mat_demand_cache`, `_material_demand_cache`, `_demand_by_tag_cache`, `_demand_by_emp_key_cache`, `_stock_throttle_cache/_sig`, `_standing_terms_cache`, `_electricity_load_ids_cache`, `_land_freight_inputs_cache`, `__dict__['_coppice_increment']` (`economy_materials.py:78,407,450`, `economy_electricity.py:349,431,511,514`, `economy_freight.py:125,228,424`); all reset by `_reset_economic_caches` (`economy.py:256-274`).

Detected by the cache scan in this module's mixin files: `engine/economy_electricity.py:349 _electricity_load_ids_cache`, `engine/economy_electricity.py:431 _material_demand_cache`, `engine/economy_electricity.py:514 _stock_throttle_cache`, `engine/economy_electricity.py:511 _stock_throttle_sig`, `engine/economy_freight.py:424 _demand_by_emp_key_cache`, `engine/economy_freight.py:125 _demand_by_tag_cache`, `engine/economy_freight.py:228 _land_freight_inputs_cache`, `engine/economy_materials.py:78 __dict__[_coppice_increment]`, `engine/economy_materials.py:407 _annual_mat_demand_cache`, `engine/economy_materials.py:186 _commod_ledger_cache`, `engine/economy_materials.py:210 _done_memo_store`, `engine/economy_materials.py:199 _material_commod_map_cache`, `engine/economy_materials.py:223 _producers_memo_store`, `engine/economy_materials.py:450 _standing_terms_cache`.
