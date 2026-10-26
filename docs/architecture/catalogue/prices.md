# Module `prices`

Calculated prices: the material price table, cost books, entry cost ratios.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 4 / 0 |
| Old methods and properties owned (after regrouping) | 15 |
| Of those, referenced from another module's mixin code | 5 (1 classed read-only or pure by Appendix B, 4 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 7 (5 from mixins, 2 only from outside) |
| Views per used name | 0.57 |
| Views that replace exactly one referenced method and no field (one-to-one) | 3 of 4 |
| Views of other modules it reads | 14, from 6 modules |
| Commands of other modules it sends | 0 |

**Existing surface and files.** Engine: `IncumbentPricesMixin`, `ProducerCostsMixin`, price helpers in `MaterialSupplyMixin`; function modules `solve_prices.py`, `solve_prices_core.py`, `solve_prices_reach.py`, `solve_prices_round.py`, `prices.py`, `making_cost.py`, `long_run_costs.py`, `entry_cost.py`, `rent_standin.py`, `energy_prices.py`, `solve_cache.py`. The solver reads almost nothing from `Sim` (`grep -ohE '\b(self|sim)\.[a-zA-Z_]+' sim/engine/solve_prices*.py | sort | uniq -c`).

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `MaterialSupplyMixin` | `sim/engine/economy_materials.py` | 3 | 2 |
| `IncumbentPricesMixin` | `sim/engine/incumbent_prices.py` | 4 | 1 |
| `ProducerCostsMixin` | `sim/engine/producer_costs.py` | 8 | 2 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_banded_market_rate`, `_cost_book`, `_founder_concern_offers`, `_material_commodity_map`, `_reference_entry`, `concern_cost_ratio`, `entry_cost_ratio`, `materials_of_commodity`.

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
| `material_prices` | table | no | The calculator-backed price table: cost of a kg of each material in the home coin. | `_material_prices`, `_price_tables`, `material_price_basis` | - | `workforce.wage`, `finance.market_rate`, `production.techniques_in_use`, `materials.material_supply` | `prices` | 15 |
| `material_price` | keyed | no | Cost per kg of one material key or curated commodity (None if unpriceable). | `_material_price_per_kg`, `_priced_key`, `_material_commodity_map` | - | `material_prices` | `prices` | 4 |
| `cost_ratios` | keyed | no | Entry cost, floor and concern cost against the incumbent price, by commodity or concern. | `entry_cost_ratio`, `commodity_floor_ratio`, `concern_cost_ratio`, `materials_of_commodity` | - | `material_prices`, `production.running` | `prices` | 2 |
| `concern_offers` | quote | no | The founder's concern as an offer on the book. | `founder_concern_offers` | - | `cost_ratios` | - | 1 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `cost_ratios`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 5 methods are referenced from other modules' mixin code: 5 are replaced by a view here, 0 by a command. 2 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 7 used names, 7 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `founder_concern_offers`.

## (d) Commands

None: this module owns no state that others change; it only publishes views.

## (e) Reads and sends

Reads (views of other modules), by provider:

- `finance`: `finance.market_rate` (input of prices.material_prices, market_rate)
- `knowledge`: `knowledge.techniques_held` (projects.granted)
- `markets`: `markets.household_prices` (goods_market.household_prices); `markets.others_trade` (goods_market.offered_by); `markets.trade_quote` (goods_market)
- `materials`: `materials.material_pool` (_material_tag); `materials.material_supply` (input of prices.material_prices)
- `production`: `production.concern_market` (concern_baskets_now); `production.revenue_estimate` (venture_ramp); `production.running` (input of prices.cost_ratios, is_venture, projects.operating); `production.techniques_in_use` (input of prices.material_prices, techniques_in_use)
- `workforce`: `workforce.labour_market` (labour.money_per_labour_hour); `workforce.staff` (labour); `workforce.wage` (input of prices.material_prices)

Sends: none.

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- none of its own: tables are rebuilt when `market` closes and techniques change

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| engine/(function modules) | 6 | `_priced_key`, `_material_prices`, `_material_price_per_kg`, `_price_tables` |
| ui | 1 | `material_price_basis` |
| engine/agents_port* | 1 | `_material_prices` |
| engine/economy_port* | 1 | `_material_prices` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `material_price_basis`, `_normalize_material_name`; engine function modules: `_material_tag` 6, `_priced_key` 2, `_material_prices` 2.

## (h) Hard spots and caches

- The solver is an iterated fixed point over producers' costs and input prices (`solve_prices_round.py`); it stays inside this module as one computation that returns a table, reading wages, rates and techniques as views.
- Four hand-made caches key on different stamps: `_incumbent_table_cache`, `_price_tables_cache`, `_material_prices_cache`, `_cost_book_cache` (`incumbent_prices.py:57-77`, `producer_costs.py:79`) plus `solve_cache.py`/`identity_cache.py`; they become one version per view.
- Price depends on techniques in use (`price_epoch`, production) and production's revenue depends on price: a cycle prices <-> production through `techniques_in_use`/`material_prices`; broken only because techniques change at project completion, not within the year. Flagged in README.
- Price levels per country (`home_price_level`, `partner_price_level`) live in coin; prices reads them for partner tables.

Caches and version counters held today (feed for task 1.2):

- `_incumbent_table_cache`, `_price_tables_cache`, `_material_prices_cache`, `_cost_book_cache`
- `sim/engine/solve_cache.py` and `identity_cache.py` (identity-keyed memo of solver inputs)

Detected by the cache scan in this module's mixin files: `engine/incumbent_prices.py:57 _incumbent_table_cache`, `engine/incumbent_prices.py:77 _material_prices_cache`, `engine/incumbent_prices.py:65 _price_tables_cache`, `engine/producer_costs.py:79 _cost_book_cache`.
