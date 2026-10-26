# Module `freight`

Transport: freight modes and costs, carriers, traders' economics, route dues.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 4 / 1 |
| Old methods and properties owned (after regrouping) | 50 |
| Of those, referenced from another module's mixin code | 10 (1 classed read-only or pure by Appendix B, 9 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 14 (10 from mixins, 4 only from outside) |
| Views per used name | 0.29 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 4 |
| Views of other modules it reads | 15, from 8 modules |
| Commands of other modules it sends | 0 |

**Existing surface and files.** Existing: `sim/geography/freight_cost.py`, `sea_freight.py`, `route_dues.py`; `sim/agents/trader.py`, `route_dues_pay.py`. Engine: `ForeignRoutesMixin`, `DomesticHaulMixin`, `ForeignTradersMixin`, `RouteDuesMixin`, material freight in `FreightMixin`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `FreightMixin` | `sim/engine/economy_freight.py` | 6 | 0 |
| `ForeignRoutesMixin` | `sim/engine/foreign_routes.py` | 17 | 6 |
| `DomesticHaulMixin` | `sim/engine/domestic_haul.py` | 9 | 1 |
| `ForeignTradersMixin` | `sim/engine/foreign_traders.py` | 14 | 3 |
| `RouteDuesMixin` | `sim/engine/route_dues.py` | 4 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_build_carrier_models`, `_capital_per_merchant`, `_cargo_class`, `_carrier_feed_material`, `_carriers_per_house`, `_domestic_flow_imbalance`, `_domestic_flow_ledger`, `_domestic_haul_mode`, `_foreign_flow_imbalance`, `_haul_route`, `_households_loanable_funds`, `_land_freight_physical_inputs`, `_material_source_tiles`, `_merchant_own_capital`, `_restock_days`, `_route_cargo_loss_share`, `_route_cargo_tonnes`, `_route_carriers`, `_route_houses`, `_route_voyage_years`, `_sea_crew`, `_share_delivered_on`, `_share_in_rate`, `_train_carrier`, `_unjoined_haul`, `domestic_cargo_cost_share`, `domestic_haul_dues_per_tonne`, `domestic_haul_money_per_tonne`, `land_freight_money_per_tonne_km`, `material_freight_cost_per_kg`, `material_freight_distance_km`, `material_freight_factor`, `material_haul_route`, `route_dues_by_holder`, `route_dues_per_tonne_by_mode`, `route_dues_treasury`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| none: this module owns derived values only, no stored field | | | |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `route_cost` | quote | no | Freight cost and handling per tonne for a route and mode, domestic and foreign; the carriage of a material. | `_foreign_route`, `_haul_route`, `_material_route`, `_route_freight_per_tonne`, `_freight_mode_costs`, `_freight_handling_costs`, `_with_carried_provisions`, `material_carriage_per_tonne`, `material_freight_cost_per_kg`, `material_freight_distance_km`, `domestic_haul_money_per_tonne`, `land_freight_money_per_tonne_km` | - | `land.transport`, `land.tile_facts`, `workforce.wage`, `prices.material_price`, `finance.market_rate` | - | 5 |
| `carrier_models` | table | no | The carrier models (animals, ships, crews) and their feed. | `_carrier_models`, `_train_carrier`, `_sea_crew` | - | `prices.material_price` | `freight` | 1 |
| `trader_economics` | keyed | no | A route's trader cost, margin, cycle, cargo loss. | `_agent_cost_per_tonne`, `_cargo_lost_share`, `_trader_cost_share`, `_trader_margin_share`, `_trader_cycle_years`, `_route_cargo_loss_share` | - | `route_cost`, `finance.market_rate` | `freight` | 3 |
| `route_dues` | table | no | Dues per tonne by mode, the treasury's take and by holder. | `route_dues_per_tonne_by_mode`, `route_dues_treasury`, `route_dues_by_holder`, `domestic_haul_dues_per_tonne` | - | `land.tile_owner` | `freight` | 0 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `carrier_models`, `route_dues`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 10 methods are referenced from other modules' mixin code: 10 are replaced by a view here, 0 by a command. 4 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 14 used names, 14 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_cargo_lost_share`, `_trader_cost_share`, `_trader_cycle_years`, `_trader_margin_share`, `route_dues_treasury`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `PayRouteDues` | payer, route, tonnes | `pay_route_dues`. Methods: `pay_route_dues` | `sim/agents/route_dues_pay.py`, `sim/engine/route_dues.py` | none: always applies | - |

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.state)
- `finance`: `finance.market_rate` (input of freight.route_cost, input of freight.trader_economics, market_rate)
- `foreign_trade`: `foreign_trade.lift` (_route_capital_per_lift_tonne, _route_lift_years_per_tonne, foreign_lift_capacity_tonnes); `foreign_trade.partners` (economy.foreign_market_book, foreign_economies)
- `land`: `land.tile_facts` (geography, geography.route_km_to, geography.source_tiles, input of freight.route_cost ...); `land.tile_owner` (input of freight.route_dues, tile_owner); `land.transport` (economy.improvements, held_and_running, input of freight.route_cost)
- `markets`: `markets.agent_economy` (economy, economy.agent)
- `prices`: `prices.material_price` (_material_price_per_kg, input of freight.carrier_models, input of freight.route_cost); `prices.material_prices` (_material_prices)
- `seats`: `seats.seat_party` (seat_party)
- `workforce`: `workforce.labour_market` (labour.market, labour.national_trade_population); `workforce.living_cost` (HOURS_PER_PERSON_YEAR); `workforce.staff` (labour); `workforce.wage` (input of freight.route_cost, labour.wage_per_hour)

Sends: none.

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- none of its own

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| engine/(function modules) | 6 | `material_carriage_per_tonne`, `_trader_margin_share`, `_cargo_lost_share`, `_trader_cycle_years`, `_foreign_route`, `_agent_cost_per_tonne` |
| engine/economy_port* | 2 | `_freight_mode_costs` |
| agents | 1 | `pay_route_dues` |
| engine/agents_port* | 1 | `pay_route_dues` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/agents: `pay_route_dues`; economy_port: `_freight_mode_costs` 2; engine functions: `material_carriage_per_tonne`, `_trader_margin_share`, `_cargo_lost_share`, `_trader_cycle_years`, `_foreign_route`, `_agent_cost_per_tonne`.

## (h) Hard spots and caches

- Private (underscore) methods are the real interface here (`_foreign_route`, `_agent_cost_per_tonne` are called from living_stock, coin and the economy port): they become the QUOTE views.
- Route choice reads the foreign flow imbalance (`_foreign_flow_imbalance`, `_domestic_flow_imbalance`), a ledger of tonnes moved each year in `geography.flow_ledger`: write path from foreign_trade to freight.

Caches and version counters held today (feed for task 1.2):

- `_carrier_models_cache` (`foreign_routes.py:101`)
- `__dict__['_material_haul_routes']` (`domestic_haul.py:56`)

Detected by the cache scan in this module's mixin files: `engine/domestic_haul.py:56 __dict__[_material_haul_routes]`, `engine/foreign_routes.py:101 _carrier_models_cache`.
