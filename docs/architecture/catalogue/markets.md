# Module `markets`

Orders and market outcomes: goods market quotes, clearing, household demand, goods-category factors, the agent economy record.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

**Update (markets port task).** The goods market object (`goods_market.py`, `goods_offers.py`, `goods_pricing.py`, `goods_imports.py`) and the port over the agent economy (`port.py`, `port_*.py`) are the module's: `Markets.setup()` builds `economy` and `goods_market`, which read the game through `PortWorld` (`port_world.py`, `port_world_foreign.py`), one member per view the module declares in `module_spec.py`. `Sim.economy` and `Sim.goods_market` are forwarders (`sim/engine/forward_markets.py`). `border_duty_per_tonne` and `unit_mass_kg` are the module's views. Still bridged (`sim/engine/bridge_markets.py`): the household need model (`household_demand_units`, `household_basket`, `market_demand.py`), `home_household_tonnes` and `partner_household_demand` (`partner_demand.py`), `settlement_tiles` and `labour_need_shares` (workforce), `material_serves_a_need`, `border_terms` (the relations store), and the command `RepriceOpeningMoney`.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 8 / 5 |
| Old methods and properties owned (after regrouping) | 33 |
| Of those, referenced from another module's mixin code | 6 (4 classed read-only or pure by Appendix B, 2 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 83 (6 from mixins, 15 only from outside) |
| Views per used name | 0.10 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 8 |
| Views of other modules it reads | 20, from 13 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 5 |

**Existing surface and files.** Existing: `sim/economy/` (181 files; `api.py` 489 lines, 57 functions; 51 distinct `economy.<member>` names in 92 uses outside it), `sim/world/market.py` (static book). Engine: `GoodsMixin`, `MarketClearingMixin`, `MarketDemandMixin`, `StaticBookBasketMixin`, `MarketAbsorptionMixin`, `EconomyPortMixin` and 24 `economy_port*.py` files, `goods_market*.py` (25 members, 48 outside uses).

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `GoodsMixin` | `sim/engine/economy_goods.py` | 9 | 0 |
| `MaterialSupplyMixin` | `sim/engine/economy_materials.py` | 3 | 0 |
| `MarketAbsorptionMixin` | `sim/engine/economy_absorption.py` | 1 | 0 |
| `MarketClearingMixin` | `sim/engine/market_clearing.py` | 10 | 3 |
| `MarketDemandMixin` | `sim/engine/market_demand.py` | 8 | 2 |
| `StaticBookBasketMixin` | `sim/engine/static_book_basket.py` | 1 | 0 |
| `EconomyPortMixin` | `sim/engine/economy_port.py` | 1 | 1 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_household_demand_now`, `_market_conditions`, `_market_flow_figures`, `_market_outcome`, `economy_size_ratio`, `goods_reach_factor`, `household_demand_ratio`, `household_demand_ratios`, `household_income_hours_per_capita`, `household_real_income_ratio`, `income_factor`, `static_book_basket`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `MarketsWorld` and a per-seat dataclass `MarketsSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.agent_economy` | world | foreign_trade 3, <engine-functions> 1 | foreign_trade 2 |
| `state.economy.market_book` | world | <engine-functions> 1 | - |
| `state.economy.market_flows` | world | <engine-functions> 2 | - |
| `state.economy.money_from_economy` | world | - | <engine-functions> 1 |
| `state.holdings.market_pressure` | seat | polity 1 | polity 1 |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `household_prices` | keyed | no | What a household pays per unit of each good now (home unit price, cost prices). Replaces `goods_market.household_prices`, `household_cost_prices`, `home_unit_price`. | `goods_market.household_prices`, `goods_market.household_cost_prices`, `goods_market.home_unit_price` | - | `prices.material_prices` | `goods` | 7 |
| `trade_quote` | quote | yes | What buying or selling a quantity at the market would cost or fetch, and the limit. Replaces `goods_market.quote`, `quote_buy`, `purchase_cost`, `can_be_bought`, `sale_limits`. | `material_trade_quote`, `goods_market`, `goods_market.quote`, `goods_market.quote_buy`, `goods_market.purchase_cost`, `goods_market.can_be_bought`, `goods_market.sale_limits`, `goods_market.settle_import`, `goods_market.commodity_is_unsourced` | - | `household_prices`, `others_trade` | - | 15 |
| `others_trade` | table | no | What other actors sold and bought this year, by commodity; the stamp of that. Replaces `goods_market.others_offers`, `others_sold_tonnes`, `others_bought_tonnes`, `others_stamp`, `offered_by`. | `goods_market.others_offers`, `goods_market.others_sold_tonnes`, `goods_market.others_bought_tonnes`, `goods_market.others_stamp`, `goods_market.offered_by`, `goods_market.bought_tonnes`, `goods_market.drawn_tonnes` | - | - | `goods` | 4 |
| `market_state` | keyed | no | One good's year: sold, unsold, unmet, price ratio, capacity, floor; from the economy's record. | `market_state`, `_market_outcome`, `_market_conditions`, `_floor_ratio`, `_market_flows`, `_market_entry`, `_market_flow_figures`, `_open_market_book` | `economy.market_book`, `economy.market_flows` | - | `goods` | 7 |
| `goods_category_factors` | keyed | no | Price ratio, factor and entrants' factor by goods category; the essential-goods price ratio. | `goods_category_factor`, `goods_category_factor_with_entrants`, `goods_category_price_ratio`, `essential_price_ratio`, `income_factor`, `_goods_category_state`, `_nodes_in_cat`, `_goods_category_ratios`, `goods_reach_factor` | - | `household_demand`, `production.running`, `actors.concern_counts` | `goods` | 4 |
| `household_demand` | table | no | Household demand ratios, new goods, real income and economy size. | `household_demand_ratios`, `household_new_goods_units`, `_opening_population`, `household_income_hours_per_capita`, `household_real_income_ratio`, `economy_size_ratio`, `household_demand_ratio`, `_household_demand_now` | - | `demography.population`, `workforce.labour_market` | `goods` | 3 |
| `market_absorption` | keyed | no | How much of a category's output the market absorbs. | `market_absorption_by_category`, `static_book_basket` | - | `household_demand` | `goods` | 1 |
| `agent_economy` | keyed | no | Prices, volumes, producers and memory of the agent economy (the `economy` handle's members). Replaces 51 `economy.<member>` names (92 uses): `agent_prices_at`, `agent_traded_volumes`, `agent_market_record`, `producers_stamp`, ... | `economy`, `economy.api`, `economy.agent`, `economy.agent_prices_at`, `economy.agent_prices`, `economy.producers_stamp`, `economy.material_prices`, `economy.agent_traded_volumes`, `economy.materials_in`, `economy.agent_seat_sale_outlook`, `economy.flow_rates`, `economy.goods_market`, `economy.households_cohort`, `economy.households_orders`, `economy.inventory`, `economy.market_areas`, `economy.market_memory`, `economy.merchants`, `economy.opening`, `economy.producers`, `economy.producers_close`, `economy.tile_costs`, `economy.agent_producers_by_good`, `economy.producer_capacities`, `economy.flush_record`, `economy.agent_offered_tonnes`, `economy.open_agent`, `economy.agent_market_record`, `economy.run_agent_year`, `economy.agent_need_floor_costs_at`, `economy.main_material_of`, `economy.trade_quote`, `economy.goods`, `economy.commodity_of`, `economy.output_value`, `economy.agent_producer_capacity_tonnes`, `economy.agent_opening_basket`, `economy.agent_volume_baseline`, `economy.agent_trades_good`, `economy.concern_upkeep` | `economy.agent_economy`, `economy.money_from_economy`, `holdings.market_pressure` | `materials.material_supply`, `ledger.balance` | `goods` | 21 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `market_absorption`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 6 methods are referenced from other modules' mixin code: 6 are replaced by a view here, 0 by a command. 15 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 83 used names, 21 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 62 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_market_conditions`, `_market_entry`, `_market_flow_figures`, `_market_flows`, `_market_outcome`, `_open_market_book`, `market_absorption_by_category`, `market_state`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `Buy` | party, material, tonnes | `buy_material_stock` / `GoodsMarket.buy`: money out (ledger), tonnes in (ledger). Methods: `goods_market.buy`, `buy_material_stock` | `sim/engine/goods_market_api.py:41,61` | `market_closed`, `cannot_afford`, `not_sold_here` | - |
| `Sell` | party, material, tonnes | `sell_material_stock` / `GoodsMarket.sell`. Methods: `goods_market.sell`, `sell_material_stock` | `sim/engine/goods_market_api.py:45,61` | `market_closed`, `no_stock`, `no_buyer` | - |
| `NoteDraw` | commodity, tonnes | `goods_market.note_draw`, `reset_draws`: the throttle's draw on the market's standing offer. Methods: `goods_market.note_draw`, `goods_market.reset_draws`, `goods_market.snapshot_flows`, `goods_market.restore_flows` | `sim/engine/economy_electricity.py:505` | none: always applies | - |
| `ClearYear` | year | `_step_market`: the close of the year's clearing, written into `market_flows` and `market_book`. Methods: `_step_market` | `sim/engine/market_clearing.py:47`, `sim/engine/goods_market_api.py:145` | none: always applies | `economy.market_flows`, `economy.market_book`, `economy.agent_economy`, `economy.money_from_economy`, `holdings.market_pressure` |
| `StageOrder` | agent, good, quantity, side | `note_sale`, `note_purchase` for staged orders, and a trader-cargo leg posted into the agent economy. | `sim/engine/economy_port_seats.py:45-46`, `sim/engine/trader_cargo.py:30,78` | `unknown_good` | `economy.agent_economy` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `economy.agent_economy`: 3 sites: `sim/engine/trader_cargo.py:30` (.setdefault()), `sim/engine/trader_cargo.py:78` (.pop()), `sim/engine/trader_cargo.py:30` (.setdefault())
- `economy.market_flows`: 1 site: `sim/engine/goods_market_api.py:145`
- `economy.money_from_economy`: 1 site: `sim/engine/opening_money.py:16`
- `holdings.market_pressure`: 2 sites: `sim/labour/labour_bondage.py:277`, `sim/engine/core_step_phases.py:419`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.concern_counts` (actor_concerns_in, actor_market_version, input of markets.goods_category_factors)
- `demography`: `demography.population` (input of markets.household_demand, pop_scale)
- `hazards`: `hazards.output_factor` (economy.output_factor)
- `knowledge`: `knowledge.techniques_held` (projects.done_year, projects.granted)
- `land`: `land.tile_facts` (world_map)
- `ledger`: `ledger.balance` (input of markets.agent_economy); `ledger.goods_stock` (_commodity_ledger)
- `materials`: `materials.material_pool` (_material_tag); `materials.material_supply` (_society_output_tonnes, input of markets.agent_economy)
- `mechanics`: `mechanics.effect` (effect_factor)
- `prices`: `prices.concern_offers` (founder_concern_offers); `prices.cost_ratios` (commodity_floor_ratio); `prices.material_prices` (_material_prices, input of markets.household_prices)
- `production`: `production.concern_market` (ledger_concern_rows); `production.revenue_estimate` (workshop_output); `production.running` (input of markets.goods_category_factors, projects.operating)
- `reporting`: `reporting.real_output` (economy.output_per_head)
- `seats`: `seats.acting_seat` (goods_market.acting, goods_market.acting_party_id)
- `workforce`: `workforce.labour_market` (input of markets.household_demand, labour.market, labour.money_per_labour_hour); `workforce.staff` (labour)

Sends (commands of other modules):

- `coin`: `Revalue`
- `demography`: `RecordFood`
- `foreign_trade`: `ClosePartnerBooks`
- `land`: `BuildWay`
- `reporting`: `RecordIndicator`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `begin_world_year`: `_open_market_book`
- `market`: `_open_market_book`, `economy.run_agent_year` (`market_clearing.py:196-197`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| engine/agents_port* | 50 | `economy`, `goods_market`, `market_state`, `goods_category_factor_with_entrants`, `goods_category_factor`, `_nodes_in_cat`, `goods_category_price_ratio`, `_goods_category_state` |
| engine/economy_port* | 45 | `economy`, `goods_market`, `_market_flows` |
| engine/(function modules) | 29 | `_market_flows`, `economy`, `goods_market`, `_market_entry`, `market_state`, `_step_market` |
| constants.py | 20 | `economy` |
| ui | 13 | `material_trade_quote`, `goods_market`, `economy`, `essential_price_ratio`, `buy_material_stock`, `sell_material_stock`, `market_absorption_by_category` |
| economy | 7 | `economy` |
| mods | 3 | `economy` |
| engine/ui* | 2 | `goods_market`, `_goods_category_ratios` |
| labour | 1 | `economy` |
| agents | 1 | `economy` |
| engine/saveload* | 1 | `economy` |
| engine/mod* | 1 | `economy` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

constants.py: 20 reads of the economy handle at import; engine agents_port*: 50; economy_port*: 45; sim/ui: 7; mods: 3. `sim/economy` is the largest outside surface (51 members).

## (h) Hard spots and caches

- Two clearings for home goods: the engine's static commodity book (`market_clearing.py`) and the economy's order book; STATE_OWNERSHIP_MAP.md 'What is left of 507 Stage 6'. The module owns both until the static book is deleted; views must say which.
- `Economy` is built from the record and handed `Sim` through `EconomyPort` (24 files); ports pass state back and forth in the year (`economy_port_year.py:98-376`). Every port function is a declared read or command.
- Clearing runs a whole year inside one phase (the `market` phase) and is iterative (price/quantity rounds); it writes goods and money through `PostBatch`/`MoveGoods` to ledger and wages to workforce.
- The goods-category caches key on `operating_version`, year and `actor_market_version`.

Caches and version counters held today (feed for task 1.2):

- `_goods_cat_state_cache`, `_goods_category_ratios_cache`, `_income_factor_cache`, `_goods_mkt_op_factor_cache`, `_nodes_by_cat_cache` (`economy_goods.py:359-695`)
- `_market_outcome_cache` (`market_clearing.py:132`), `_household_demand_cache` (`market_demand.py:159`), `_static_book_basket_cache` (`static_book_basket.py:37`)
- `__dict__['_economy_port']` (`economy_port.py:418`), `_sale_index`, `_seat_inputs`, `_seat_offered`, `_capacity_cache` (`economy_port_year.py:98,265,364,365`), `_home_prices_cache` (`goods_market_offers.py:83`)

Detected by the cache scan in this module's mixin files: `engine/economy_goods.py:359 _goods_cat_state_cache`, `engine/economy_goods.py:440 _goods_category_ratios_cache`, `engine/economy_goods.py:695 _goods_mkt_op_factor_cache`, `engine/economy_goods.py:646 _income_factor_cache`, `engine/economy_goods.py:394 _nodes_by_cat_cache`, `engine/economy_port.py:418 __dict__[_economy_port]`, `engine/market_clearing.py:132 _market_outcome_cache`, `engine/market_demand.py:159 _household_demand_cache`, `engine/static_book_basket.py:37 _static_book_basket_cache`.
