# Module `production`

What runs: operating techniques and capability, revenue and upkeep of concerns, industry experience, techniques in use.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 7 / 4 |
| Old methods and properties owned (after regrouping) | 74 |
| Of those, referenced from another module's mixin code | 34 (14 classed read-only or pure by Appendix B, 20 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 47 (34 from mixins, 13 only from outside) |
| Views per used name | 0.15 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 7 |
| Views of other modules it reads | 36, from 20 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 1 |

**Existing surface and files.** Existing: `sim/agents/business*.py`, `sim/agents/firm.py` (firms hold concerns; Complaints 510 and 514). Engine: `ProductionMixin` (27 methods), `CapabilityMixin`, `ConcernVolumeMixin`, `ConcernBookSalesMixin`, `TechniquesInUseMixin`, `IndustryDepthMixin`, `IndustryConcernMixin`, `NodeRederiveMixin`, `FounderSalesMixin`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `MechanicsMixin` | `sim/engine/mechanics.py` | 1 | 1 |
| `MaterialSupplyMixin` | `sim/engine/economy_materials.py` | 1 | 0 |
| `ProductionMixin` | `sim/engine/economy_production.py` | 23 | 16 |
| `ConcernVolumeMixin` | `sim/engine/concern_volume.py` | 5 | 1 |
| `ConcernBookSalesMixin` | `sim/engine/concern_book_sales.py` | 4 | 0 |
| `TechniquesInUseMixin` | `sim/engine/techniques_in_use.py` | 4 | 2 |
| `IndustryDepthMixin` | `sim/engine/industry_depth.py` | 18 | 5 |
| `IndustryConcernMixin` | `sim/engine/industry_concern.py` | 4 | 0 |
| `CapabilityMixin` | `sim/engine/projects_capability.py` | 7 | 6 |
| `FounderSalesMixin` | `sim/engine/founder_sales.py` | 3 | 0 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 2 | 0 |
| `NodeRederiveMixin` | `sim/engine/node_rederive.py` | 3 | 3 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_compute_revenue_uncached`, `_concern_prices_in_hours`, `_concern_ratios`, `_concern_sale_setup`, `_revenue_upkeep_candidates`, `add_industry_years`, `attempt_worker_years_by_trade`, `capability_factor`, `concern_book_scale`, `concern_input_availability`, `concern_learning_ratio`, `concern_sells_on_book`, `concern_value_ratio`, `concern_worker_years_this_year`, `days_from_producers`, `fade_industry_tenure`, `founding_staff_by_trade`, `founding_worker_years`, `industry_experience`, `industry_tenure`, `industry_tenure_by_trade`, `opening_worker_years_by_node`, `producer_capacity_tonnes`, `seed_opening_industry_experience`, `techniques_epoch`, `tenure_leavers_share`, `tenure_weights`, `upkeep_by_concern`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `ProductionWorld` and a per-seat dataclass `ProductionSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.nodes_money_per_labour_hour` | world | - | <engine-functions> 1 |
| `state.economy.technique_first_run` | world | - | - |
| `state.economy.technique_record_started` | world | - | - |
| `state.projects.industry_opening_rate` | seat | - | - |
| `state.projects.industry_seeded` | seat | - | - |
| `state.projects.operating` | seat | <ui> 15, ventures 14, <engine-functions> 4, diffusion 3, core 2, seats 2, +9 more | seats 1, hazards 1 |
| `state.projects.tenure` | seat | - | - |
| `state.projects.tenure_headcount` | seat | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `running` | table | yes | The seat's techniques and capabilities now running, and which are ventures or concern nodes. | `running`, `running_with_mechanic`, `is_venture`, `is_concern_node`, `capability_gaps`, `_practisable`, `_practice_set` | `projects.operating` | `knowledge.techniques_held`, `mechanics.capability_sets` | `operating` | 23 |
| `revenue_estimate` | table | yes | This year's revenue of the seat's concerns (capacity, sources, ramp-up). | `revenue`, `revenue_capacity`, `estimated_revenue`, `concern_revenue`, `revenue_sources`, `held_trade`, `venture_ramp`, `still_ramping`, `workshop_output` | - | `running`, `prices.material_prices`, `markets.goods_category_factors`, `materials.resource_throttle`, `workforce.staff`, `hazards.output_factor` | `operating`, `done` | 11 |
| `upkeep` | table | yes | Running costs of concerns and institutions (by concern, institutions' places). | `upkeep`, `upkeep_by_concern`, `institution_upkeep`, `institution_places` | - | `running`, `prices.material_prices`, `workforce.wage` | `operating` | 8 |
| `institution_units` | keyed | yes | Units, ceiling and unit cost of an institution (school, workshop, ...). | `institution_units`, `institution_unit_ceiling`, `institution_unit_cost` | - | `running`, `demography.population`, `workforce.literacy_capacity` | `operating` | 5 |
| `techniques_in_use` | table | no | Techniques in use in society and how widely they have spread; epochs for caches. | `techniques_in_use`, `techniques_spread`, `price_epoch`, `techniques_epoch`, `_society_held_techs` | `economy.technique_first_run`, `economy.technique_record_started` | `actors.concern_counts`, `running` | `operating`, `done` | 4 |
| `concern_market` | quote | yes | A concern's sales basis, book offer, takings and market factor. | `concern_goods_have_market`, `node_output_market_factor`, `concern_sale_basis`, `concern_takings`, `concern_book_offer`, `concern_sells_on_book`, `concern_book_inputs_cost`, `concern_baskets_now`, `concern_volume_ratio`, `concern_value_ratio`, `ledger_concern_rows`, `quote_concern_sale` | - | `markets.goods_category_factors`, `prices.cost_ratios` | - | 7 |
| `industry_depth` | keyed | yes | Depth, tenure and scale ceiling of an industry; whether it runs without its founder. | `industry_depth`, `industry_scale_ceiling`, `industry_tenure`, `concern_runs_without_founder`, `learn_from_failed_attempt`, `after_failed_attempts`, `industry_experience`, `producer_capacity_tonnes` | `projects.tenure`, `projects.tenure_headcount`, `projects.industry_seeded`, `projects.industry_opening_rate` | `workforce.staff` | `operating` | 3 |

**Coverage.** 34 methods are referenced from other modules' mixin code: 31 are replaced by a view here, 3 by a command. 13 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 47 used names, 46 are covered by a view or command through the method itself, 1 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `concern_baskets_now`, `concern_book_inputs_cost`, `concern_book_offer`, `concern_goods_have_market`, `concern_revenue`, `concern_runs_without_founder`, `concern_sale_basis`, `concern_sells_on_book`, `concern_takings`, `concern_value_ratio`, `concern_volume_ratio`, `estimated_revenue`, `industry_depth`, `industry_experience`, `industry_scale_ceiling`, `institution_unit_cost`, `ledger_concern_rows`, `node_output_market_factor`, `quote_concern_sale`, `revenue`, `revenue_capacity`, `revenue_sources`, `still_ramping`, `techniques_spread`, `venture_ramp`, `workshop_output`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `SetOperating` | seat, node, running | Adds and discards from `projects.operating`. | `sim/engine/society_hazards.py:606`, `sim/engine/core_step_phases.py:588`, `sim/engine/projects_completion.py`, `sim/agents/household.py:361` | `not_done` | `projects.operating` |
| `AccrueExperience` | seat, node, worker_years | `accrue_industry_experience`, `add_industry_years`, `seed_opening_industry_experience`. Methods: `accrue_industry_experience` | `sim/engine/industry_depth.py` | none: always applies | `projects.tenure`, `projects.tenure_headcount`, `projects.industry_seeded`, `projects.industry_opening_rate` |
| `RederiveNodes` | held techniques | `refresh_derived_nodes` rewrites `self.nodes` (the shared tree) after society's techniques change. Methods: `refresh_derived_nodes`, `_remember_derived_gates` | `sim/engine/node_rederive.py:38-39` | none: always applies | `economy.nodes_money_per_labour_hour` |
| `SellConcern` | seat, node, buyer | `sell_concern`. Methods: `sell_concern` | `sim/engine/founder_sales.py` | `not_running`, `no_buyer` | - |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `economy.nodes_money_per_labour_hour`: 1 site: `sim/engine/opening_money.py:33`
- `projects.operating`: 3 sites: `sim/agents/household.py:361`, `sim/engine/society_hazards.py:606` (.discard()), `sim/engine/core_step_phases.py:588` (.discard())

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.active_firms, actors.concerns_of_active_firms, actors.get ...); `actors.concern_counts` (actor_market_version, concern_set_version, input of production.techniques_in_use)
- `coin`: `coin.price_level` (home_price_level)
- `demography`: `demography.population` (input of production.institution_units, pop_scale)
- `diffusion`: `diffusion.literacy` (literacy)
- `disease`: `disease.coverage` (coverage_nodes, units_for_coverage)
- `finance`: `finance.debt_status` (household.bondage_years_left)
- `hazards`: `hazards.output_factor` (economy.output_factor, input of production.revenue_estimate)
- `knowledge`: `knowledge.techniques_held` (done_in_order, has, input of production.running, projects.done ...)
- `land`: `land.transport` (economy.improvements)
- `ledger`: `ledger.acting_balance` (household.capital)
- `markets`: `markets.agent_economy` (economy, economy.agent_prices_at, economy.agent_producer_capacity_tonnes, economy.agent_producers_by_good ...); `markets.goods_category_factors` (input of production.concern_market, input of production.revenue_estimate); `markets.household_prices` (goods_market.home_unit_price); `markets.trade_quote` (goods_market)
- `materials`: `materials.resource_throttle` (input of production.revenue_estimate)
- `mechanics`: `mechanics.capability_sets` (CAPABILITY_INSTITUTIONS, NOT_OPERATING_BENEFIT, SCALABLE_INSTITUTIONS, input of production.running); `mechanics.effect` (effect_sum); `mechanics.mechanic` (mechanic)
- `polity`: `polity.standing` (household.reputation)
- `prices`: `prices.cost_ratios` (input of production.concern_market); `prices.material_price` (_priced_key); `prices.material_prices` (_material_prices, input of production.revenue_estimate, input of production.upkeep)
- `projects`: `projects.running_gates` (gate_blocked)
- `reporting`: `reporting.real_output` (economy.output_per_head, real_output_per_head)
- `seats`: `seats.founder` (founder.founder_alive); `seats.seat_party` (seat_party)
- `ventures`: `ventures.venture_crew` (venture_foreman, venture_hands_founder_staffed); `ventures.venture_quote` (venture_capex, venture_real_earnings, venture_real_upkeep)
- `workforce`: `workforce.hour_commitments` (household.wage_hours_this_year); `workforce.hours_available` (labour.director_hours_committed); `workforce.labour_market` (economy.agent_worker_years_by_recipe, labour.market, labour.people_who_exist); `workforce.literacy_capacity` (input of production.institution_units, labour.LITERACY_REFERENCE_GENERAL); `workforce.living_cost` (HOURS_PER_PERSON_YEAR); `workforce.staff` (household.directors_extra, household.employees, household.freedmen, household.slaves ...); `workforce.wage` (input of production.upkeep, labour.wage_signature)

Sends (commands of other modules):

- `workforce`: `CommitHours`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `begin_world_year`: `refresh_derived_nodes` (`core_step_phases.py:118-123`)
- `money_seat`: venture revenue and running costs (`step_phase_money.py:48-52`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 67 | `operating`, `is_venture`, `upkeep`, `revenue`, `revenue_sources`, `institution_units`, `running`, `revenue_capacity` |
| engine/agents_port* | 16 | `revenue`, `concern_baskets_now`, `concern_takings`, `node_output_market_factor`, `upkeep`, `is_venture`, `industry_depth`, `industry_scale_ceiling` |
| engine/economy_port* | 5 | `techniques_in_use`, `concern_book_offer`, `concern_book_inputs_cost`, `techniques_spread` |
| agents | 4 | `concern_takings`, `upkeep` |
| engine/(function modules) | 3 | `is_concern_node`, `revenue`, `upkeep` |
| engine/saveload* | 1 | `refresh_derived_nodes` |
| engine/ui* | 1 | `_practice_set` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `operating` 15, `is_venture` 12, `upkeep` 10, `revenue` 10, `revenue_sources`, `institution_units`; agents_port: `revenue` 3, `concern_baskets_now` 3, `concern_takings` 3, `node_output_market_factor`; economy_port: `techniques_in_use`, `concern_book_offer`.

## (h) Hard spots and caches

- `revenue` is the most-called derived value (23 mixin calls, UI 10) with the largest hand-made cache: key built from done, operating and workforce versions and the price epoch (`economy_production.py:167-188`), reset by `_reset_economic_caches`. As a derived view it has five input channels from four modules.
- `refresh_derived_nodes` writes into the shared tree (`self.nodes`), which every module reads as static data. The tree must become a view with a version (`tree`), or be re-derived only at defined points.
- Revenue and prices form a cycle (see prices); `venture_ramp`/`still_ramping` add a within-year dependence on the year counter.
- Float sums over the done/operating sets rely on `done_in_order`; the new views must iterate sorted.

Caches and version counters held today (feed for task 1.2):

- `_revenue_cache_key/_val`, `_rev_up_candidates_cache`, `_practice_cache`, `_cap_factor`, `_done_seq` (`economy_production.py:187-601`, `economy.py:221`)
- `_techniques_in_use_cache`, `_techniques_spread_cache` (`techniques_in_use.py:42,59`)

Detected by the cache scan in this module's mixin files: `engine/economy_production.py:526 _practice_cache`, `engine/economy_production.py:601 _rev_up_candidates_cache`, `engine/economy_production.py:188 _revenue_cache_key`, `engine/economy_production.py:187 _revenue_cache_val`, `engine/techniques_in_use.py:42 _techniques_in_use_cache`, `engine/techniques_in_use.py:59 _techniques_spread_cache`.
