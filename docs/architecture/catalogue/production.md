# Module `production`

What runs: operating techniques and capability, revenue and upkeep of concerns, industry experience, techniques in use.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

**Moved (task 1.5, `sim/production/`).** The module publishes the views of `READS_BY_OWNER` under the names the bridges used, plus the keyed and quote views the old `Sim` names forward to (`sim/production/module_spec.py` lists them; `sim/engine/forward_production.py` is the forwarders). Its commands are `AccrueExperience` and `LearnFromFailure`. It owns `ProductionSeat` (tenure, tenure_headcount, industry_seeded, industry_opening_rate). Left in the engine: `node_rederive.py` and `economy.nodes_money_per_labour_hour` (they rewrite the shared tree and are priced by engine code), `node_defaults.py` (the tree's field defaults), `concern_scan_run.py` (a diagnostic over the whole game), `held_works.py` (land's `held_and_running`), and `founder_sales.py`, `works.py`, `benefactions.py`, `venture_net_loss.py` (ventures and works move later). `projects.operating` stays where it is: `sim/agents/household.py` writes it and the version counters. The module reads the projects record, the household counters, the tree and the economy through the views of their owners (the engine bridge answers `projects_operating` and `running_versions`), keeps its revenue, capability, practice and candidate memos itself per seat (`caches.SeatMemos`), and the engine hooks drop them by sending `RefreshDoneCaches`, `RefreshOperatingCaches` and `ForgetRevenueCaches`. It reads no `legacy_*` view.

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

## Width review

Measure: `python3 tools/measure/module_graph.py --modules` (reads, sends and modules depended on); the reads by publisher are
`python3 -c "from sim.production.module_spec import READS_BY_OWNER as table; [print(owner, names) for owner, names in table.items()]"`
(regrouped under the module that publishes each view). The module sends two commands; its width is all reads. Grouping the package's
files by the views each reads shows two parts: the earnings (`revenue.py`, `book_sales.py`, `concern_market.py`, `upkeep.py`,
`volume.py`, and the pure rules beside them, `node_revenue*.py`, `node_upkeep.py`, `node_output.py`, `node_capital.py`,
`revenue_ledger.py`, `concern_sales.py`, `concern_earnings.py`) and the learning (`capability.py`, `depth.py`, `learning.py`,
`techniques.py`, `caches.py`).

### What it depends on, by what it asks

| Asks of | What for | Reads and sends |
|---|---|---|
| scenario, content, seats | The year, the setting, the civilisation, the trade families, who acts | `year`, `game_setting`, `civilisation`; `trade_family`; `acting_seat`, `founder` |
| workforce | The people a concern runs on and what an hour costs | `staff`, `staff_version`, `headcount`, `hour_commitments`, `hours_available`, `wage_signature`, `market_annual_wage`, `standing_job_pay`, `money_per_labour_hour`, `base_tile`, `people_who_exist`, `hours_per_person_year`, `literacy_references`; send `SetWageHoursSold` (a revenue quote with no hours sold) |
| ventures | The plants: which run, their size, capital, earnings and upkeep, their foreman | `operating`, `operating_version`, `institution_units_version`, `venture_opened_year`, `venture_size`, `venture_capex`, `venture_real_earnings`, `venture_real_upkeep`, `venture_foreman`, `venture_hands_founder_staffed`, `coverage`, `units_for_coverage` |
| knowledge, mechanics, land | What the seat holds, the mechanics that gate a run, what is built | `techniques_held`, `techniques_version`, `techniques_granted`, `done_year`, `tree_nodes`, `category_trait`; `capability_sets`, `mechanic`, `running_mechanics`, `effect_sum`; `built_ways`, `held_techniques` |
| markets, prices | What the agent economy sells and pays, and the price books | markets `agent_prices_at`, `agent_seat_sale_outlook`, `agent_trades_good`, `agent_producers_by_good`, `agent_worker_years_by_recipe`, `home_unit_price`; prices `held_goods_prices_in_hours`, `price_index`, `done_memo`, `producers_memo`, `material_prices`, `commodity_record` |
| actors, diffusion, demography | The firms' concerns, the spread of techniques, the population | actors `concern_versions`, `concerns_of_active_firms`, `firm_concern_holdings`; diffusion `literacy`, `techniques_spread`, send `NoteFirstRuns`; demography `pop_scale`, `population`, `farm_holdings` |
| polity, hazards, reporting, finance, coin, projects | The inputs of the year's revenue: state funding, the output factor, output per head, the debt, the price level, which projects gate a run | polity `standing`, `state_funding`; hazards `output_factor`; reporting `real_output_per_head`; finance `debt_status`; coin `home_price_level`; projects `gate_blocked` |

### Findings

**(a) Mirror views.**

- None merged. Three pairs are a value and its change counter, read together to key a memo rather than to answer a question:
  `techniques_held` with `techniques_version` (knowledge), `operating` with `operating_version` and `institution_units_version`
  (ventures), `staff` with `staff_version` (workforce). They belong with the cache-key finding below.
- Open, not built, workforce: `market_annual_wage(trade)`, `standing_job_pay(trade)` and `wage_signature()` are read together in
  `revenue.py` for one question, what the household's own hours earn at the market wage; a `wage_work_pay` view of workforce would give
  it (finance reads `standing_job_pay` for the same). Workforce owns it.
- Open, not built, markets and prices: six reads each, in `book_sales.py`, `concern_market.py`, `learning.py`, `depth.py`. They are
  distinct questions (who produces a good, what a seat would sell, a recipe's worker-years); the views are owned by the markets and
  prices modules, whose reviews are separate.

**(b) Sub-domains that read their own set of owners.**

- The earnings part is the only part that reads content, finance, hazards, polity, reporting and seats, and sends `SetWageHoursSold`;
  the learning part is the only one that reads actors, land and projects. Proposal: a `concern_earnings` module holding the earnings
  files (`revenue.py`, `book_sales.py`, `concern_market.py`, `concern_sales.py`, `concern_earnings.py`, `upkeep.py`, `volume.py`,
  `node_revenue.py`, `node_revenue_census.py`, `node_revenue_market.py`, `node_upkeep.py`, `node_output.py`, `node_capital.py`,
  `node_payback_diagnostic.py`, `revenue_ledger.py`, `bondage_workshop_rules.py`) and the views `revenue_estimate`, `revenue_capacity`,
  `estimated_revenue`, `revenue_sources`, `founder_wage_income`, `upkeep`, `upkeep_by_concern`, `concern_revenue`, `workshop_output`,
  `concern_market`, `held_trade`, `concern_*` and `node_output_market_factor`, `basket_market_factor`, `venture_ramp`,
  `ramp_share_at_full_depth`. `production` would keep what is run and learned (`running`, `capability_*`, `industry_*`,
  `techniques_*`, `practice_set`, `institution_*`) and drop content, finance, hazards, polity, reporting and seats; the earnings module
  reads production for `running` and `institution_units`. The views have many readers outside (see section (g)), so the split changes
  their owner name in those readers' spec lines.

**(c) Pass-through dependencies.**

- The revenue memo key (`revenue()` in `revenue.py`, and `techniques_epoch` plus `home_price_level` in `techniques.py`) reads
  `debt_status` (finance), `farm_holdings` (demography), `standing` (polity), `founder` (seats), `home_price_level` (coin),
  `hour_commitments` and `wage_signature` (workforce) only so that a change to any of them drops the cached
  total (and `concern_versions` of actors, in the techniques epoch). The total itself is computed from `venture_real_earnings` (ventures), which is where those inputs are used; production
  knows the inputs of another module's computation. Finance, and in this module the only edge to it, exists for this alone. Not built:
  dropping an input from the key would return a stale total, so the fix is for the owner of the computation to publish one change
  counter that covers its inputs (`venture_earnings_version`, in ventures), and for production to key on it; the key's other entries
  (`year`, `pop_scale`, `real_output_per_head`, `output_factor`, `state_funding`) are read by the compute itself and stay.
- Nothing else is read only to hand it on: `hazards.output_factor`, `polity.state_funding` and the markets and prices reads are multiplied
  into the figures the module answers.

### What was done, and why each remaining edge is needed

Nothing was changed in code for this module: no read is unused, none is a mirror one owner publishes twice, and the one pass-through
(the memo key) cannot be trimmed without moving the cache to the owner of the figure it keys, which is a change of ventures' views.
Each remaining edge is an input of a figure the module answers: what runs and what it is worth (ventures, knowledge, mechanics, land),
what it earns and costs (workforce, markets, prices, polity, hazards, reporting, coin), what an industry has learned (actors, diffusion,
demography, workforce) and which projects gate a run (projects). The cycles with workforce, ventures and projects are economic: workforce
sells hours that revenue counts, ventures price the plants that revenue sums, projects ask whether a run is gated.
