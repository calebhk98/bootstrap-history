# Module `living_stock`

Herds and defence stores: holding, growing, buying, smuggling and drawing animals and arms.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 4 / 5 |
| Old methods and properties owned (after regrouping) | 45 |
| Of those, referenced from another module's mixin code | 9 (2 classed read-only or pure by Appendix B, 7 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 22 (9 from mixins, 9 only from outside) |
| Views per used name | 0.18 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 4 |
| Views of other modules it reads | 29, from 16 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 2 |

**Existing surface and files.** Engine only: `LivingStockMixin` and seven siblings (`living_stock*.py`), `DefenceStoresMixin`, `FoodReliefMixin`. Prototype 2.1 in MODULE_MIGRATION_TASKS.md.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `FoodReliefMixin` | `sim/engine/food_relief.py` | 2 | 1 |
| `LivingStockMixin` | `sim/engine/living_stock.py` | 8 | 4 |
| `LivingStockOpeningMixin` | `sim/engine/living_stock_opening.py` | 4 | 1 |
| `LivingStockTradeMixin` | `sim/engine/living_stock_trade.py` | 4 | 0 |
| `LivingStockSmugglingMixin` | `sim/engine/living_stock_smuggling.py` | 9 | 0 |
| `LivingStockYearlyMixin` | `sim/engine/living_stock_yearly.py` | 4 | 1 |
| `LivingStockGrowthMixin` | `sim/engine/living_stock_growth.py` | 6 | 0 |
| `DefenceStoresMixin` | `sim/engine/defence_stores.py` | 8 | 2 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_partner_holding`, `_partner_taken`, `_punish_smuggler`, `_smuggle_terms`, `_smuggling_chance`, `_smuggling_draw`, `_stock_key`, `bank_works_output`, `buy_stock_from_partner`, `draw_defence_stores`, `endemic_keeping`, `endemic_stock_loss`, `garrison_claims`, `garrison_share`, `growth_labour`, `magazine_share`, `nursery_room_units`, `opening_herd_units`, `partner_quote_per_tonne`, `partner_state_reach`, `pasture_room_kg`, `pay_growth_labour`, `relief_kilograms_per_year`, `smuggle_stock_from_partner`, `society_herds`, `stock_missing`, `stock_place`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `LivingStockWorld`, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.society_herds` | world | agriculture 1 | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `stock_status` | keyed | yes | What a living stock holds and lacks: held, missing, gates, whether holds are met, needed by a node. | `stock_held`, `stock_missing`, `stock_gates`, `stock_holds_met`, `held_living_stock`, `stock_needed_by`, `_stock_key`, `geography.stock_place`, `geography.pasture_room_kg`, `geography.endemic_stock_loss`, `geography.nursery_room_units` | `economy.society_herds` | `ledger.goods_stock`, `agriculture.wild_stock` | `herds` | 4 |
| `stock_quote` | quote | yes | Cost of buying or smuggling a stock from a partner, per tonne and in total. | `stock_purchase_quote`, `stock_smuggle_quote`, `partner_quote_per_tonne`, `partner_state_reach` | - | `foreign_trade.partners`, `foreign_trade.foreign_supply`, `freight.trader_economics`, `freight.route_cost`, `markets.trade_quote`, `polity.state_reach` | - | 1 |
| `garrison` | keyed | yes | Garrison, magazine and claims of a venture; supply gap against a counter. | `venture_garrison`, `garrison_claims`, `garrison_share`, `magazine_share`, `counter_supply_gap` | - | `ventures.venture_crew`, `production.running`, `mechanics.effect` | `herds` | 3 |
| `relief` | table | no | Food relief in kcal per day and kilograms per year. | `relief_kcal_per_day`, `relief_kilograms_per_year` | - | `mechanics.effect` | - | 1 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `relief`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 9 methods are referenced from other modules' mixin code: 5 are replaced by a view here, 4 by a command. 9 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 22 used names, 16 are covered by a view or command through the method itself, 0 through a field alias, 2 are year-phase hooks and 4 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `counter_supply_gap`, `held_living_stock`, `magazine_share`, `partner_quote_per_tonne`, `stock_gates`, `stock_held`, `stock_holds_met`, `stock_missing`, `stock_needed_by`, `stock_purchase_quote`, `stock_smuggle_quote`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `GrantStock` | seat, stock, units | `grant_stock`, `grant_opening_stock`, `grant_opening_herds`. Methods: `grant_stock`, `grant_opening_stock`, `grant_opening_herds` | `sim/engine/living_stock.py`, `sim/engine/living_stock_opening.py`, `sim/engine/core.py` | `unknown_stock` | `economy.society_herds` |
| `ChangeHeld` | seat, stock, delta | `change_stock`: births, deaths, endemic loss. Methods: `change_stock` | `sim/engine/living_stock_yearly.py:73`, `sim/engine/living_stock_growth.py` | `no_room` | `economy.society_herds` |
| `BuyStock` | seat, partner, stock, units | `buy_stock_from_partner`, `settle_stock_purchase`: sends Buy, SettleFlow. Methods: `buy_stock_from_partner`, `settle_stock_purchase` | `sim/engine/living_stock_trade.py` | `partner_refused`, `cannot_afford` | - |
| `SmuggleStock` | seat, partner, stock, units | `smuggle_stock_from_partner`, `settle_stock_smuggle`, `_punish_smuggler`: sends ChangeStanding. Methods: `smuggle_stock_from_partner`, `settle_stock_smuggle` | `sim/engine/living_stock_smuggling.py` | `caught`, `partner_refused` | - |
| `DrawDefenceStores` | seat, node | `draw_defence_stores`, `bank_works_output`, `step_defence_stores`. | `sim/engine/defence_stores.py` | none: always applies | - |

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.world_for)
- `agriculture`: `agriculture.farm_sites` (geography.held_pasture_kg); `agriculture.wild_stock` (economy.wild_stock, input of living_stock.stock_status)
- `coin`: `coin.price_level` (partner_price_level)
- `foreign_trade`: `foreign_trade.foreign_supply` (input of living_stock.stock_quote); `foreign_trade.partners` (_foreign_economy_facts, input of living_stock.stock_quote, partner_civ, partner_countries ...)
- `freight`: `freight.route_cost` (_material_route, input of living_stock.stock_quote); `freight.trader_economics` (_agent_cost_per_tonne, _cargo_lost_share, _trader_cost_share, input of living_stock.stock_quote)
- `knowledge`: `knowledge.techniques_held` (projects.done)
- `land`: `land.build_quote` (partner_gate_refusal); `land.tile_facts` (geography)
- `ledger`: `ledger.acting_balance` (capital, household.capital); `ledger.goods_stock` (_material_stock, input of living_stock.stock_status, material_stock_t); `ledger.goods_stock_opening` (_material_opening_stock)
- `markets`: `markets.agent_economy` (economy, economy.producer_capacities); `markets.household_prices` (goods_market.home_unit_price); `markets.trade_quote` (goods_market, goods_market.settle_import, input of living_stock.stock_quote)
- `materials`: `materials.material_pool` (_material_tag)
- `mechanics`: `mechanics.effect` (effect_holds, input of living_stock.garrison, input of living_stock.relief); `mechanics.mechanic` (_effect_terms, mechanic)
- `polity`: `polity.standing` (household.scandal_last_year, scandal, scandal_last_year); `polity.state_reach` (input of living_stock.stock_quote)
- `production`: `production.institution_units` (institution_units); `production.running` (input of living_stock.garrison, is_venture, projects.operating, running_with_mechanic)
- `seats`: `seats.acting_seat` (goods_market.acting, goods_market.acting_party_id)
- `ventures`: `ventures.venture_crew` (input of living_stock.garrison)
- `workforce`: `workforce.labour_market` (labour.market); `workforce.living_cost` (HOURS_PER_PERSON_YEAR); `workforce.staff` (household.employees, labour)

Sends (commands of other modules):

- `foreign_trade`: `SettleFlow`
- `polity`: `ChangeStanding`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `living_stock`
- `defence_stores`

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 10 | `stock_needed_by`, `stock_held`, `stock_gates`, `held_living_stock`, `stock_purchase_quote`, `settle_stock_purchase`, `stock_smuggle_quote`, `settle_stock_smuggle` |
| engine/(function modules) | 2 | `step_living_stock`, `step_defence_stores` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `stock_needed_by` 2, `stock_held` 2, `stock_gates`, `held_living_stock`, `stock_purchase_quote`, `settle_stock_purchase`, `stock_smuggle_quote`, `settle_stock_smuggle`; project starting reads `stock_held`, `grant_stock`, `change_stock`.

## (h) Hard spots and caches

- Small (about 650 lines in ten files) and read by almost nothing, but it reaches out widely: 29 views from 16 modules (list in (e)); the mixin-level references are foreign_trade 15, markets 8, land 6, mechanics 5, ledger 7, freight 5 (mostly private methods). It is the first test of the 15-read limit.
- A herd is not this module's state: it is a row in the founder's tonnes ledger under `_stock_key(material)`, and `change_stock` writes the ledger, the opening snapshot and nulls `_stock_throttle_sig` (`living_stock_yearly.py:70-76`). The module owns `economy.society_herds` and the rates in `data/world/living_stock.json`; every change of a held herd is the ledger command `ChangeStock`, so 2.1 needs the ledger's `ChangeStock` (part of 2.2) first.
- `step_living_stock` runs a loop over materials in sorted order with a shared, shrinking pasture room and a mutable `society_herds`; it is expected values with no dice (docstring), so the equivalence tool compares exact numbers. The per-material rule is already a plain function (`stock_dynamics.next_units`, `founder_billed_growth`); the loop and the room carry-over become one plain function from (held, rates, room, society herd) to (after, grown, billed).
- `check_unheld_stock` is a registered start check (`@blocker_kind("supply")`, `living_stock.py:15`): the module provides it to the project module's `start_checks` extension point instead of being called by name.
- Writes scandal through the forwarding property (`living_stock_smuggling.py`) and edits the founder's tonnes ledger directly (`living_stock_yearly.py:73`), both to become commands.
- `_stock_throttle_sig` is written here (`living_stock_yearly.py:76`) to invalidate the materials memo: after migration it is the `goods_stock` version.

Caches and version counters held today (feed for task 1.2):

- `_stock_throttle_sig` (`living_stock_yearly.py:76`)

Detected by the cache scan in this module's mixin files: `engine/living_stock_yearly.py:76 _stock_throttle_sig`.
