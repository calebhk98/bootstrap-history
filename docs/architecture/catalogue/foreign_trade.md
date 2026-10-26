# Module `foreign_trade`

Trade with partner countries: their economies, supply, payments in coin, lift capacity, actors' trade books.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 4 / 5 |
| Old methods and properties owned (after regrouping) | 40 |
| Of those, referenced from another module's mixin code | 13 (4 classed read-only or pure by Appendix B, 9 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 28 (13 from mixins, 14 only from outside) |
| Views per used name | 0.14 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 4 |
| Views of other modules it reads | 20, from 12 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 2 |

**Existing surface and files.** Existing: `sim/world/market.py` partner books; `sim/economy/foreign.py`. Engine: `ForeignEconomiesMixin`, `ForeignCapacityMixin`, `ForeignPaymentsMixin`, `ForeignActorTradeMixin`, `TraderCargoMixin`; `foreign_economy_data.py`, `country_trade_years.py`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `ForeignEconomiesMixin` | `sim/engine/foreign_economies.py` | 9 | 7 |
| `ForeignCapacityMixin` | `sim/engine/foreign_capacity.py` | 6 | 1 |
| `ForeignPaymentsMixin` | `sim/engine/foreign_payments.py` | 8 | 4 |
| `ForeignActorTradeMixin` | `sim/engine/foreign_actor_trade.py` | 10 | 1 |
| `TraderCargoMixin` | `sim/engine/trader_cargo.py` | 7 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_foreign_can_make`, `_foreign_demand_and_make`, `_foreign_mineral_share`, `_import_offers`, `_money_per_partner_coin`, `_note_trade_value`, `_partner_outcome`, `_pay_duty`, `_pay_partner`, `_record_lift`, `_tracked_mineral`, `_true_up_trader`, `foreign_opening`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `ForeignTradeWorld`, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.capacity_pool` | world | ledger 1 | ledger 1 |
| `state.economy.foreign_actor_trade` | world | - | - |
| `state.economy.foreign_ledger` | world | coin 2 | - |
| `state.economy.foreign_market_book` | world | freight 1 | - |
| `state.economy.foreign_trade_by_year` | world | - | - |
| `state.economy.home_actor_trade` | world | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `partners` | table | no | Partner civilisations, countries, governments and refusals; partners in the agent economy; the facts of each foreign economy. | `partner_civ`, `partner_countries`, `partner_government`, `partner_refusal`, `partners_in_agent_economy`, `foreign_economies`, `_foreign_economy_facts`, `_foreign_entry`, `_commodity_materials`, `economy.foreign` | `economy.foreign_market_book` | `knowledge.techniques_held` | `partners` | 9 |
| `foreign_supply` | keyed | no | What a partner can make, supplies and its opening. | `foreign_supply_tonnes`, `foreign_opening`, `_foreign_can_make`, `_foreign_demand_and_make`, `_tracked_mineral` | `economy.foreign_market_book` | `partners`, `materials.material_supply` | `partners` | 4 |
| `lift` | table | no | Lift capacity of a route in tonnes and what is left; years and capital per lift tonne. | `_foreign_ledger`, `foreign_lift_capacity_tonnes`, `foreign_lift_left_tonnes`, `_route_lift_years_per_tonne`, `_route_capital_per_lift_tonne` | `economy.foreign_ledger`, `economy.foreign_trade_by_year`, `economy.capacity_pool` | `freight.route_cost` | `lift` | 5 |
| `actor_trade` | keyed | no | Actors' home and foreign trade books, landed cost and price response. | `actor_home_trade`, `actors_carry`, `partner_price_per_unit`, `partner_price_response`, `landed_cost`, `cargo_legs` | `economy.foreign_actor_trade`, `economy.home_actor_trade` | `partners`, `freight.trader_economics` | `actor_trade` | 2 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `actor_trade`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 13 methods are referenced from other modules' mixin code: 11 are replaced by a view here, 2 by a command. 14 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 28 used names, 27 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 1 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_foreign_entry`, `_foreign_ledger`, `foreign_lift_capacity_tonnes`, `foreign_lift_left_tonnes`, `partner_price_per_unit`, `partner_price_response`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `SettleFlow` | route, tonnes, money | `_settle_flow`, `_record_lift`, `_note_trade_value`: pays partners through ledger and notes the flow. Methods: `_settle_flow`, `close_partner_books` | `sim/engine/foreign_payments.py`, `sim/engine/living_stock_trade.py` | `lift_exhausted` | `economy.foreign_ledger`, `economy.foreign_trade_by_year` |
| `NoteActorTrade` | actor, good, tonnes, side | `note_actor_trade`, `note_actor_home_trade`. Methods: `note_actor_trade`, `note_actor_home_trade` | `sim/engine/foreign_actor_trade.py:25,42,113` | none: always applies | `economy.foreign_actor_trade`, `economy.home_actor_trade` |
| `SettleTraderCargo` | legs | `settle_trader_cargo`, `note_cargo_leg`; posts the legs to markets (StageOrder). Methods: `settle_trader_cargo`, `note_cargo_leg` | `sim/engine/trader_cargo.py:30,78` | none: always applies | - |
| `ClosePartnerBooks` | year | `close_partner_books`. Methods: `close_partner_books` | `sim/engine/foreign_actor_trade.py` | none: always applies | - |
| `ChangeCapacityPool` | key, amount | Direct edit of the capacity pool by the founder's stock sweep. | `sim/engine/economy_materials.py:772` | none: always applies | `economy.capacity_pool` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `economy.capacity_pool`: 1 site: `sim/engine/economy_materials.py:772`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.actors, actors.get)
- `coin`: `coin.coin_carriage` (coin_carriage_units); `coin.price_level` (partner_price_level)
- `finance`: `finance.market_rate` (market_rate)
- `freight`: `freight.carrier_models` (_carrier_models); `freight.route_cost` (_foreign_route, _route_freight_per_tonne, input of foreign_trade.lift); `freight.trader_economics` (input of foreign_trade.actor_trade)
- `knowledge`: `knowledge.techniques_held` (input of foreign_trade.partners, projects.done)
- `land`: `land.build_quote` (partner_gate_refusal); `land.tile_facts` (geography, geography.held_share, world_map)
- `ledger`: `ledger.goods_stock` (_commodity_ledger)
- `markets`: `markets.agent_economy` (economy.agent_economy); `markets.household_prices` (goods_market.home_unit_price, goods_market.household_prices); `markets.market_state` (_floor_ratio); `markets.trade_quote` (goods_market)
- `materials`: `materials.material_pool` (_material_tag); `materials.material_supply` (_national_output_tonnes, input of foreign_trade.foreign_supply)
- `prices`: `prices.material_prices` (_material_prices)
- `resources`: `resources.deposits` (geography.tracked_materials)
- `seats`: `seats.acting_seat` (goods_market.acting_party_id)

Sends (commands of other modules):

- `ledger`: `PayEdge`
- `markets`: `ClearYear`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `market`: `close_partner_books` (`market_clearing.py:199`); `settle_trader_cargo` runs inside the economy year (`economy_port_year.py:240`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| engine/agents_port* | 16 | `_foreign_economy_facts`, `note_actor_home_trade`, `note_actor_trade`, `partner_countries`, `foreign_economies`, `partner_price_per_unit`, `_foreign_entry`, `actor_home_trade` |
| engine/economy_port* | 14 | `foreign_economies`, `actors_carry`, `partner_civ`, `_settle_flow`, `partners_in_agent_economy`, `cargo_legs`, `settle_trader_cargo`, `partner_price_per_unit` |
| engine/(function modules) | 8 | `foreign_supply_tonnes`, `_foreign_economy_facts`, `foreign_lift_left_tonnes`, `partner_civ`, `foreign_economies`, `_commodity_materials` |
| ui | 1 | `partner_countries` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

agents_port 16 (`_foreign_economy_facts` 4, `note_actor_*`), economy_port 14 (`foreign_economies`, `actors_carry`, `partner_civ`, `_settle_flow` 2), engine functions 8.

## (h) Hard spots and caches

- `_foreign_economy_facts`, `_foreign_entry`, `_settle_flow` are underscore methods called from three modules; they are the real surface.
- Foreign trade writes `economy.agent_economy` (a markets field) in `trader_cargo.py:30,78`; that becomes a command to markets.
- `economy.capacity_pool` is written by the founder's stock sweep (ledger) as well as read here.

Caches and version counters held today (feed for task 1.2):

- `_foreign_can_make_cache`, `_foreign_demand_cache` (`foreign_capacity.py:110,134`), `_partner_civs` (`foreign_economies.py:69`), `_commodity_materials_cache`, `_foreign_facts_cache` (`foreign_economies.py:130,159`)

Detected by the cache scan in this module's mixin files: `engine/foreign_capacity.py:110 __dict__[_foreign_can_make_cache]`, `engine/foreign_capacity.py:134 __dict__[_foreign_demand_cache]`, `engine/foreign_economies.py:69 __dict__[_partner_civs]`, `engine/foreign_economies.py:159 _commodity_materials_cache`, `engine/foreign_economies.py:130 _foreign_facts_cache`.
