# Module `resources`

Extractive resources: mines, deposits, prospecting, forest and nitre beds.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 5 / 4 |
| Old methods and properties owned (after regrouping) | 63 |
| Of those, referenced from another module's mixin code | 14 (6 classed read-only or pure by Appendix B, 8 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 35 (14 from mixins, 18 only from outside) |
| Views per used name | 0.14 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 5 |
| Views of other modules it reads | 20, from 11 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 3 |

**Existing surface and files.** Existing: `sim/world/deposits.py`, `sim/geography` deposit queries. Engine: `MiningMixin` (41 methods), `MineDepositsMixin` (15), and forest/nitre in `FreightMixin` (`build_nitre`, shortage remedies).

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `FreightMixin` | `sim/engine/economy_freight.py` | 4 | 1 |
| `MiningMixin` | `sim/engine/economy_mining.py` | 40 | 10 |
| `MineDepositsMixin` | `sim/engine/mine_deposits.py` | 15 | 2 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 8 | 2 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `MINE_OPEX_PER_T`, `MINE_TRADE`, `_advance_mine_depletion`, `_capacity_naming`, `_close_worked_out`, `_deposit_base`, `_deposit_rows`, `_draw_working`, `_mine_capex_opex`, `_mine_depletion_note_from`, `_mine_labour_hours_per_tonne`, `_mine_opex`, `_mine_reference_deposits`, `_modelled_sizes`, `_priced_rows`, `_worked_before_start`, `_workings_of`, `allocate_to_deposits`, `base_mine_catalog_hint`, `deposit_remaining_tonnes`, `forest_land_ceiling`, `mine_depletion_factor_for`, `mine_land_ceiling`, `mine_operating_cost_new`, `mine_resource_id`, `mine_room_in_deposits`, `mine_tranches`, `mine_works_effects`, `mine_yield_t`, `mining_cost_scale`, `mining_cost_scale_for`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `ResourcesWorld` and a per-seat dataclass `ResourcesSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.forest_felled` | world | <engine-functions> 2 | <engine-functions> 1 |
| `state.holdings.deposit_drawn` | seat | - | - |
| `state.holdings.deposits_found` | seat | - | - |
| `state.holdings.forest_ha` | seat | projects 4, materials 4, core 2, <ui> 2, coin 1, finance 1 | - |
| `state.holdings.mine_cost_paid` | seat | - | finance 1 |
| `state.holdings.mine_pending` | seat | projects 1 | - |
| `state.holdings.mine_ready` | seat | - | - |
| `state.holdings.mine_tranches` | seat | - | - |
| `state.holdings.mines` | seat | core 2, <ui> 1 | - |
| `state.holdings.nitre_bed_m2` | seat | materials 3, core 2, <ui> 2 | projects 1 |
| `state.holdings.prospected_person_days` | seat | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `mine_catalogue` | table | yes | Mines the seat could open: catalogue hints, ceilings, quotes. | `mineable`, `mine_catalog_hint`, `mine_land_ceiling`, `mine_demand_goods`, `mine_quote` | - | `land.tile_facts`, `knowledge.techniques_held` | `mines` | 1 |
| `mine_output` | table | yes | Capacity and yield of running workings and their depletion. | `mine_capacity`, `mine_depletion_factor`, `_running_kept`, `mine_yield_t`, `mine_yield_t_for`, `mine_depletion_note`, `mine_depletion_note_for` | `holdings.mines`, `holdings.mine_pending`, `holdings.mine_ready`, `holdings.mine_tranches` | `production.running` | `mines` | 6 |
| `mine_cost` | quote | yes | Operating and capital cost of workings. | `mine_operating_cost`, `mine_operating_cost_for`, `mine_operating_cost_new`, `_mine_capex`, `MINE_OPEX_MATERIALS` | `holdings.mine_cost_paid` | `prices.material_prices`, `workforce.wage` | - | 6 |
| `deposits` | keyed | yes | Known deposits and their remaining tonnes, per resource and tile. | `found_deposits`, `partner_deposits`, `geography.mineral_scale`, `geography.mineral_shares`, `geography.tracked_materials` | `holdings.deposits_found`, `holdings.deposit_drawn`, `holdings.prospected_person_days` | `land.tile_facts` | `deposits` | 5 |
| `forest_and_nitre` | table | yes | Hectares of coppice, nitre beds m2, the price per hectare and the shortage remedy. | `shortage_remedy`, `shortage_remedy_plan`, `material_shortfall_t`, `forest_price_per_hectare`, `forest_ha`, `nitre_bed_m2` | `holdings.forest_ha`, `holdings.nitre_bed_m2`, `economy.forest_felled` | `prices.material_prices` | `forest` | 8 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `mine_catalogue`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 14 methods are referenced from other modules' mixin code: 9 are replaced by a view here, 5 by a command. 18 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 35 used names, 31 are covered by a view or command through the method itself, 1 through a field alias, 0 are year-phase hooks and 3 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `mine_land_ceiling`, `mine_quote`, `shortage_remedy`, `shortage_remedy_plan`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `OpenMine` | seat, resource, tile, scale | `open_mine`, `commission_mines`, `close_mine`, `mothball_mines`. Methods: `open_mine`, `commission_mines`, `mothball_mines`, `close_mine` | `sim/engine/economy_mining.py:721` | `not_minable`, `cannot_afford`, `deposit_unknown` | `holdings.mines`, `holdings.mine_pending`, `holdings.mine_ready`, `holdings.mine_tranches`, `holdings.mine_cost_paid` |
| `DrawDeposit` | deposit, tonnes | `draw_deposit`, `allocate_to_deposits`. Methods: `draw_deposit` | `sim/engine/mine_deposits.py (draw_deposit)`, `sim/engine/economy_port_*.py` | `deposit_empty` | `holdings.deposit_drawn` |
| `Prospect` | seat, tile, person_days | `auto_prospect`, `prospect_deposits`. Methods: `auto_prospect`, `prospect_deposits` | `sim/engine/mine_deposits.py:176` | `no_hours` | `holdings.deposits_found`, `holdings.prospected_person_days` |
| `BuyForest` | seat, hectares | `buy_forest`, `build_nitre`. Methods: `buy_forest`, `build_nitre` | `sim/engine/economy_mining.py:944`, `sim/engine/economy_freight.py:559`, `sim/engine/step_phase_project_start.py:300` | `cannot_afford` | `holdings.forest_ha`, `holdings.nitre_bed_m2`, `economy.forest_felled` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `economy.forest_felled`: 2 sites: `sim/engine/economy_port_timber.py:67`, `sim/engine/economy_port_timber.py:74`
- `holdings.mine_cost_paid`: 1 site: `sim/engine/step_phase_money.py:47`
- `holdings.mines`: 1 site: `sim/agents/household.py:380`
- `holdings.nitre_bed_m2`: 2 sites: `sim/engine/step_phase_project_start.py:301`, `sim/engine/economy_freight.py:560`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `agriculture`: `agriculture.farm_weather` (_farm_year_weather_seed)
- `knowledge`: `knowledge.techniques_held` (input of resources.mine_catalogue, projects.done, projects.granted)
- `land`: `land.tile_facts` (geography, input of resources.deposits, input of resources.mine_catalogue, world_map ...)
- `ledger`: `ledger.acting_balance` (household.capital); `ledger.goods_stock` (_material_stock)
- `materials`: `materials.material_demand` (CHARCOAL_PER_HA, _demand_by_supply_tag, annual_material_demand, demand_and_own_supply_by_material); `materials.material_pool` (_normalize_material_name); `materials.material_supply` (_material_market_tonnes); `materials.project_materials` (material_unsupplied_sentence)
- `mechanics`: `mechanics.effect` (effect_best); `mechanics.mechanic` (_effect_terms)
- `polity`: `polity.state_reach` (forest_reach, inspection_reach)
- `prices`: `prices.material_price` (_material_price_per_kg); `prices.material_prices` (input of resources.forest_and_nitre, input of resources.mine_cost)
- `production`: `production.revenue_estimate` (revenue); `production.running` (input of resources.mine_output, projects.operating, running)
- `reporting`: `reporting.event_log` (household.log)
- `workforce`: `workforce.labour_market` (labour.labour_market); `workforce.staff` (labour); `workforce.wage` (input of resources.mine_cost, labour.wage_per_hour)

Sends (commands of other modules):

- `ledger`: `PayEdge`, `ReceiveFromEdge`
- `reporting`: `RecordEvent`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `money_seat`: `mothball_mines` (`step_phase_money.py:63`); mine depletion advances with the running-cost calculation (`economy_mining.py:775`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 40 | `mine_operating_cost`, `mine_capacity`, `mine_demand_goods`, `forest_ha`, `nitre_bed_m2`, `mine_catalog_hint`, `mine_quote`, `buy_forest` |
| engine/economy_port* | 3 | `found_deposits`, `partner_deposits`, `draw_deposit` |
| engine/(function modules) | 3 | `mine_operating_cost`, `found_deposits`, `material_shortfall_t` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `mine_operating_cost` 7, `mine_capacity` 6, `mine_demand_goods` 3, `forest_ha`, `nitre_bed_m2`, `mine_quote`; economy_port: `found_deposits`, `partner_deposits`, `draw_deposit`.

## (h) Hard spots and caches

- `mine_operating_cost` is referenced from finance (9), projects (4), workforce; it reads prices and wages (`price_index`), which read `mine_capacity`: a loop between materials prices and mine output resolved by evaluation order today.
- `MiningMixin` mixes catalogue, quote and write in one 41-method class; `_running_kept` consults capability sets (production).

Caches and version counters held today (feed for task 1.2):

- `__dict__['_running_kept_tables']` (`economy_mining.py:454`)
- `_deposit_base_cache`, `_modelled_sizes_cache` (`mine_deposits.py:44,61`)

Detected by the cache scan in this module's mixin files: `engine/economy_mining.py:454 __dict__[_running_kept_tables]`, `engine/mine_deposits.py:61 __dict__[_deposit_base_cache]`, `engine/mine_deposits.py:44 __dict__[_modelled_sizes_cache]`.
