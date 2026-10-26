# Module `coin`

Coin as a metal: stock and price level, revaluation, hoarding, carriage and theft.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 5 / 3 |
| Old methods and properties owned (after regrouping) | 29 |
| Of those, referenced from another module's mixin code | 11 (2 classed read-only or pure by Appendix B, 9 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 19 (11 from mixins, 6 only from outside) |
| Views per used name | 0.26 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 5 |
| Views of other modules it reads | 25, from 13 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 2 |

**Existing surface and files.** Existing: `sim/economy/mint.py`, `metal_stock.py`, `currency.py`, `sim/agents/tuning_coinage.py`. Engine: `CoinHoardMixin`, `CoinCarriageMixin`, `CoinRevaluationMixin`, `TheftChargeMixin`, `HoldingsExposureMixin`, coin pieces of `ForeignPaymentsMixin`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `CoinRevaluationMixin` | `sim/engine/coin_revaluation.py` | 4 | 2 |
| `ForeignPaymentsMixin` | `sim/engine/foreign_payments.py` | 6 | 2 |
| `CoinHoardMixin` | `sim/engine/coin_hoard.py` | 8 | 3 |
| `CoinCarriageMixin` | `sim/engine/coin_carriage.py` | 4 | 1 |
| `TheftChargeMixin` | `sim/engine/theft_charge.py` | 5 | 3 |
| `HoldingsExposureMixin` | `sim/engine/holdings_exposure.py` | 2 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_coin_carriage_money_per_tonne`, `_home_opening_coin_units`, `_opening_coin_units`, `actor_exposure`, `charge_coin_carriage`, `coin_hoard`, `coin_metal_ratio`, `home_carriage_per_tonne`, `home_coin_stock_units`, `partner_coin_metal`, `place_of`, `steal_from`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `CoinWorld`, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.coin_metal_ratios` | world | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `coin_stock` | table | no | Coin units in circulation (home and partner), the hoard and its report, kg per unit. | `home_coin_stock_units`, `_home_opening_coin_units`, `_opening_coin_units`, `_partner_coin_opening_units`, `coin_hoard`, `coin_kg_per_unit`, `coin_hoard_report` | - | - | `coin` | 3 |
| `price_level` | keyed | no | Price level by country. | `home_price_level`, `partner_price_level` | - | `coin_stock`, `markets.market_state` | `coin` | 4 |
| `coin_metal` | table | no | Coin metal ratios by country. | `coin_metal_ratio`, `home_coin_metal`, `partner_coin_metal`, `economy.metal_stock`, `economy.currency` | `economy.coin_metal_ratios` | `prices.material_prices` | `coin` | 2 |
| `exposure` | quote | yes | How exposed a holder's wealth is to theft and visible to the state. | `actor_exposure`, `founder_exposure`, `founder_visible_scale`, `coin_keeping_cost_per_year` | - | `ledger.balance`, `polity.visible_scale`, `resources.forest_and_nitre`, `agriculture.farm_holdings` | - | 1 |
| `coin_carriage` | quote | no | The cost of carrying coin over a route. | `coin_carriage_units`, `coin_carriage_listening`, `home_carriage_per_tonne`, `_coin_carriage_money_per_tonne`, `place_of` | - | `freight.route_cost` | - | 3 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `coin_metal`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 11 methods are referenced from other modules' mixin code: 5 are replaced by a view here, 6 by a command. 6 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 19 used names, 17 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 2 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `founder_exposure`, `partner_price_level`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `ChargeKeeping` | actors | `charge_actors_for_keeping_coin`, `coin_keeping_due`. Methods: `charge_actors_for_keeping_coin`, `coin_keeping_due` | `sim/engine/step_phase_money.py:55` | none: always applies | - |
| `ChargeTheft` | holder, share | `charge_actors_for_theft`, `charge_founder_for_theft`, `plunder_founder`, `steal_from`. Methods: `charge_actors_for_theft`, `charge_founder_for_theft`, `plunder_founder` | `sim/engine/theft_charge.py` | none: always applies | - |
| `Revalue` | year | `revalue_coin_metals`. Methods: `revalue_coin_metals` | `sim/engine/coin_revaluation.py` | none: always applies | `economy.coin_metal_ratios` |

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.actors, actors.get, actors.state ...)
- `agriculture`: `agriculture.farm_holdings` (farm_stock_kg, holdings.farm_hectares, holdings.farm_stock_kg, input of coin.exposure); `agriculture.farm_land_quote` (farm_price_per_hectare)
- `finance`: `finance.capital_market` (lent_share); `finance.credit_limit` (credit_limit)
- `foreign_trade`: `foreign_trade.lift` (economy.foreign_ledger); `foreign_trade.partners` (_foreign_economy_facts, foreign_economies, partner_civ)
- `freight`: `freight.route_cost` (_freight_handling_costs, _freight_mode_costs, _with_carried_provisions, input of coin.coin_carriage)
- `land`: `land.tile_facts` (world_map, world_map.tiles); `land.transport` (held_and_running)
- `ledger`: `ledger.acting_balance` (capital, household.capital); `ledger.balance` (input of coin.exposure); `ledger.goods_stock` (_material_stock)
- `markets`: `markets.household_demand` (_opening_population); `markets.market_state` (input of coin.price_level); `markets.trade_quote` (goods_market, goods_market.quote)
- `polity`: `polity.standing` (household.eminence, household.protection); `polity.state_reach` (order_reach); `polity.visible_scale` (input of coin.exposure, visible_scale)
- `prices`: `prices.material_prices` (input of coin.coin_metal)
- `reporting`: `reporting.price_ratios` (coin_value_ratio)
- `resources`: `resources.forest_and_nitre` (forest_ha, holdings.forest_ha, input of coin.exposure)
- `workforce`: `workforce.labour_market` (labour.money_per_labour_hour); `workforce.staff` (labour, labour.headcount); `workforce.wage` (labour.opening_wage_schedule)

Sends (commands of other modules):

- `agriculture`: `RecordFarmYear`
- `ledger`: `PayEdge`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `money_seat`: `coin_keeping_due`, `charge_founder_for_theft` (`step_phase_money.py:49,56`); `charge_actors_for_keeping_coin` inside the actors' year (`society_actors.py:166`)
- `market`: `revalue_coin_metals` (`market_clearing.py:201`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| mods | 4 | `coin_keeping_cost_per_year`, `coin_kg_per_unit`, `founder_exposure`, `founder_visible_scale` |
| ui | 2 | `coin_hoard_report` |
| engine/economy_port* | 1 | `_partner_coin_opening_units` |
| engine/(function modules) | 1 | `partner_price_level` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

ui: `coin_hoard_report` 2; mods: `coin_keeping_cost_per_year`, `coin_kg_per_unit`, `founder_exposure`, `founder_visible_scale`.

## (h) Hard spots and caches

- `home_coin_stock_units` is a second tally of the society's coin, separate from the book (STATE_OWNERSHIP_MAP.md): a ledger-derived view or a deliberate duplicate.
- `actor_exposure` sums farm stock, forest, mines and material stock across modules (`holdings_exposure.py`); it is a pure derived quote over five other modules' views. Its `Exposure` lots carry `take` closures that mutate the purse, stock and granary (`holdings_exposure.py:60-85`): a read that returns write capability. The quote must return amounts only, and the theft must go through one `TakeGoods` command.

Caches and version counters held today (feed for task 1.2):

- `__dict__['_home_carriage_cache']` (`coin_carriage.py:54`)

Detected by the cache scan in this module's mixin files: `engine/coin_carriage.py:54 __dict__[_home_carriage_cache]`.
