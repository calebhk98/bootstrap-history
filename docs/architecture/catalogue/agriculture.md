# Module `agriculture`

Farming: farmland, farm weather, soil nitrogen, wild stock and food potential.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 5 / 2 |
| Old methods and properties owned (after regrouping) | 22 |
| Of those, referenced from another module's mixin code | 6 (3 classed read-only or pure by Appendix B, 3 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 24 (6 from mixins, 5 only from outside) |
| Views per used name | 0.21 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 5 |
| Views of other modules it reads | 7, from 5 modules |
| Commands of other modules it sends | 2 |

**Existing surface and files.** Existing: `sim/world/agriculture.py`, `sim/world/farming_technique.py`, `sim/world/weather_pooling.py`, `sim/geography` food functions. Engine: `FoodSupplyMixin`, `SoilNitrogenMixin`, the farm-weather methods inside `Sim` (`core.py`), farm pricing in `GoodsMixin`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `Sim` | `sim/engine/core.py` | 8 | 2 |
| `GoodsMixin` | `sim/engine/economy_goods.py` | 2 | 1 |
| `FounderSalesMixin` | `sim/engine/founder_sales.py` | 1 | 0 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 4 | 2 |
| `FoodSupplyMixin` | `sim/engine/food_supply.py` | 4 | 1 |
| `SoilNitrogenMixin` | `sim/engine/soil_nitrogen_year.py` | 5 | 1 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_cap_pooled_farm_weather_cells`, `_compute_farm_tile_arable_share`, `_compute_farm_weather_cells`, `_compute_farm_weather_correlation_cholesky`, `_draught_manure_kg`, `_gathering_caps`, `_raw_farm_weather_cells`, `_rotation_cropped_share`, `sell_farm`, `society_food_potential`, `soil_nitrogen_factors`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `AgricultureWorld` and a per-seat dataclass `AgricultureSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.soil_nitrogen` | world | - | - |
| `state.economy.wild_stock` | world | living_stock 2 | - |
| `state.holdings.farm_cleared_hectares` | seat | - | - |
| `state.holdings.farm_hectares` | seat | coin 1, <ui> 1 | - |
| `state.holdings.farm_hours_needed` | seat | <engine-functions> 1 | - |
| `state.holdings.farm_last_harvest_kg` | seat | <engine-functions> 1 | demography 1 |
| `state.holdings.farm_last_marginal_product` | seat | - | demography 1 |
| `state.holdings.farm_last_shortfall_kg` | seat | - | demography 1 |
| `state.holdings.farm_stock_kg` | seat | coin 2, demography 1 | core 1, demography 1, coin 1 |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `farm_holdings` | table | yes | Hectares farmed, stock in kg, the last harvest, marginal product, shortfall and hours needed. Replaces the forwarding properties `farm_hectares`, `farm_stock_kg`. | `farm_stock_kg` | `holdings.farm_hectares`, `holdings.farm_stock_kg`, `holdings.farm_cleared_hectares`, `holdings.farm_last_shortfall_kg`, `holdings.farm_last_harvest_kg`, `holdings.farm_last_marginal_product`, `holdings.farm_hours_needed` | - | `farm` | 5 |
| `farm_weather` | keyed | no | The growing-season weather multiplier by tile for the year. | `farm_weather_by_tile`, `_pooled_farm_weather_multiplier`, `_farm_year_weather_seed` | - | `land.tile_facts` | `weather` | 3 |
| `farm_sites` | table | no | Tiles farmable by the society and the territory refresh. | `farm_sites`, `refresh_farm_territory`, `geography.crop_sites`, `geography.food_kcal_by_source`, `geography.game_food_sources`, `geography.huntable_kcal`, `geography.held_pasture_kg`, `geography.soil_nitrogen_factors` | - | `land.tiles_owned_by` | `farm` | 3 |
| `farm_land_quote` | quote | no | Price per hectare of farmland and the cost to invest. | `farm_price_per_hectare` | - | `prices.material_prices` | - | 2 |
| `wild_stock` | table | no | Wild game and gatherable stock by tile. | `geography.take_hunt`, `geography.regrow_wild_stock`, `geography.step_soil_nitrogen` | `economy.wild_stock`, `economy.soil_nitrogen` | - | `farm` | 1 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `wild_stock`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 6 methods are referenced from other modules' mixin code: 6 are replaced by a view here, 0 by a command. 5 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 24 used names, 8 are covered by a view or command through the method itself, 1 through a field alias, 2 are year-phase hooks and 13 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_farm_year_weather_seed`, `_pooled_farm_weather_multiplier`, `farm_weather_by_tile`, `refresh_farm_territory`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `InvestFarm` | seat, hectares | `invest_farm`, `sell_farm`. Methods: `invest_farm`, `sell_farm` | `sim/engine/economy_goods.py:562-565`, `sim/engine/founder_sales.py:65-66` | `cannot_afford`, `no_land` | `holdings.farm_hectares` |
| `RecordFarmYear` | seat, harvest_kg, marginal_product, shortfall_kg | Year results from the demographic step and the farm workforce allocation. Methods: `labour.set_farm_area`, `labour.allocate_farm_workforce`, `labour.apply_land_clearing`, `labour.stochastic_round` | `sim/engine/demographic_recovery.py:155-166`, `sim/labour/labour_allocation.py:213,357` | none: always applies | `holdings.farm_stock_kg`, `holdings.farm_last_harvest_kg`, `holdings.farm_last_marginal_product`, `holdings.farm_last_shortfall_kg`, `holdings.farm_cleared_hectares`, `holdings.farm_hours_needed` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `holdings.farm_cleared_hectares`: 1 site: `sim/labour/labour_allocation.py:213`
- `holdings.farm_hectares`: 2 sites: `sim/engine/founder_sales.py:65`, `sim/engine/economy_goods.py:565`
- `holdings.farm_hours_needed`: 1 site: `sim/labour/labour_allocation.py:357`
- `holdings.farm_last_harvest_kg`: 1 site: `sim/engine/demographic_recovery.py:165`
- `holdings.farm_last_marginal_product`: 1 site: `sim/engine/demographic_recovery.py:166`
- `holdings.farm_last_shortfall_kg`: 1 site: `sim/engine/demographic_recovery.py:164`
- `holdings.farm_stock_kg`: 3 sites: `sim/engine/core.py:423` (assign (alias)), `sim/engine/demographic_recovery.py:155` (assign (alias)), `sim/engine/holdings_exposure.py:89` (assign (alias))

## (e) Reads and sends

Reads (views of other modules), by provider:

- `land`: `land.tile_facts` (geography, input of agriculture.farm_weather, world_map); `land.tiles_owned_by` (input of agriculture.farm_sites)
- `ledger`: `ledger.acting_balance` (household.capital)
- `living_stock`: `living_stock.stock_status` (economy.society_herds)
- `prices`: `prices.material_prices` (input of agriculture.farm_land_quote)
- `workforce`: `workforce.labour_market` (economy.society_labour_hours, labour.farming_technique); `workforce.staff` (labour)

Sends (commands of other modules):

- `ledger`: `PayEdge`, `ReceiveFromEdge`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `begin_world_year`: `refresh_farm_territory`
- `wild_stock`
- `soil_nitrogen`

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 3 | `invest_farm`, `farm_hectares`, `farm_price_per_hectare` |
| engine/economy_port* | 3 | `farm_sites`, `_pooled_farm_weather_multiplier`, `farm_weather_by_tile` |
| engine/(function modules) | 2 | `step_wild_stock`, `step_soil_nitrogen` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `farm_hectares`, `invest_farm`, `farm_price_per_hectare`; economy_port: `farm_sites`, `farm_weather_by_tile`; `sim/geography` has 27 members used from the engine, several for food (`food_kcal_by_source`, `huntable_kcal`, `take_hunt`, `regrow_wild_stock`).

## (h) Hard spots and caches

- Farm weather is a Cholesky-pooled draw from the shared random source (`core.py` `_compute_farm_weather_*`); order of draws must not change (CLAUDE.md, order must not depend on history). It is a keyed view per year but its first read consumes randomness: model it as a phase that fills it, not a lazily computed view.
- `farm_stock_kg` is written by Sim, demography and coin exposure code (three writers). Only agriculture may write it.
- Workforce allocates farm labour (`allocate_farm_workforce`, `set_farm_area` in `sim/labour`) and writes `farm_cleared_hectares` and `farm_hours_needed` directly (`labour_allocation.py:213,357`).

Caches and version counters held today (feed for task 1.2):

- `_farm_weather_cells`, `_farm_weather_correlation_cholesky`, pooled-cell caches in `Sim` (`core.py`)
- `_farm_arable_ceiling`, `_farm_ladder` (`soil_nitrogen_year.py`)
