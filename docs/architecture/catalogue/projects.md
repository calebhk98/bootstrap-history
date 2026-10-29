# Module `projects`

The lifecycle of a project: can it start, what it costs, progress, completion and failure.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 8 / 7 |
| Old methods and properties owned (after regrouping) | 96 |
| Of those, referenced from another module's mixin code | 18 (11 classed read-only or pure by Appendix B, 7 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 42 (18 from mixins, 24 only from outside) |
| Views per used name | 0.19 |
| Views that replace exactly one referenced method and no field (one-to-one) | 2 of 8 |
| Views of other modules it reads | 42, from 16 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 18 |

**Existing surface and files.** Engine: `StartingMixin` (33 methods), `ProgressMixin`, `CompletionMixin`, `BlockersMixin`, `ExclusionsMixin`, `OpenGateMixin`, `RunningGatesMixin`, `RebuildMixin`, `ProjectCostTailMixin`, `ProjectStartPhaseMixin`, `ProjectProgressPhaseMixin`, and the cost methods of `EconomyMixin`; function modules `project_funding.py`, `project_throttle.py`, `planner.py`, `path_search.py`, `completion_rules.py`, `failure_cause.py`, `projects_review.py`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `EconomyMixin` | `sim/engine/economy.py` | 6 | 6 |
| `CreditMixin` | `sim/engine/economy_credit.py` | 1 | 0 |
| `ProjectCostTailMixin` | `sim/engine/projects_cost_tail.py` | 1 | 0 |
| `BlockersMixin` | `sim/engine/blockers.py` | 6 | 0 |
| `RunningGatesMixin` | `sim/engine/projects_running_gates.py` | 8 | 4 |
| `OpenGateMixin` | `sim/engine/projects_open_gate.py` | 2 | 1 |
| `StartingMixin` | `sim/engine/projects_starting.py` | 33 | 1 |
| `ExclusionsMixin` | `sim/engine/projects_exclusions.py` | 2 | 1 |
| `ProgressMixin` | `sim/engine/projects_progress.py` | 8 | 0 |
| `CompletionMixin` | `sim/engine/projects_completion.py` | 9 | 1 |
| `RebuildMixin` | `sim/engine/projects_rebuild.py` | 6 | 1 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 10 | 0 |
| `ProjectStartPhaseMixin` | `sim/engine/step_phase_project_start.py` | 2 | 2 |
| `ProjectProgressPhaseMixin` | `sim/engine/step_phase_projects.py` | 7 | 1 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_cash_covers_start`, `_check_absent_trades`, `_check_already_active`, `_check_already_done`, `_check_arrears`, `_check_craft_staff`, `_check_credit_frozen`, `_check_foreign_only`, `_check_missing_prereqs`, `_check_needs_first`, `_check_needs_held_herd`, `_check_none_left_trades`, `_check_people_exist`, `_check_scholar_staff`, `_check_social_approval`, `_check_substitution`, `_check_unobtainable`, `_check_win_condition`, `_classify_check`, `_complete`, `_control_relief_multiplier`, `_dependents_index`, `_fail_attempt`, `_is_power_capability`, `_missing_prereq_entries`, `_money_refusal`, `_patron_advice`, `_power_gate_text`, `_project_progress_afford_gate`, `_project_progress_finish`, `_project_progress_labour_and_bill`, `_project_progress_offer_hours`, `_project_progress_trade_gate`, `_record_substitution_gap`, `_retry_calendar_retain`, `_running_gate_index`, `_step_progress_project`, `_substitution_group_best`, `bounties_paid`, `failure_severity`, `goal_closure_ids`, `goal_effect_lines`, `initialize_project`, `is_being_rebuilt`, `lose_what_was_risked`, `payment_schedule_years`, `rebuild_retained_share`, `rebuild_survivals`, `running_gate_text`, `settle_cost_tail`, `staffing_open_refusal`, `substitution_quality`, `unmet_running_gates`, `ways_short`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `ProjectsSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.household.bounties_paid` | seat | - | - |
| `state.projects.active` | seat | <ui> 49, <engine-functions> 8, workforce 6, materials 4, core 2, hazards 2, +3 more | core 2, hazards 2 |
| `state.projects.bountied` | seat | workforce 1, <ui> 1 | - |
| `state.projects.excluded` | seat | <ui> 6 | <ui> 1 |
| `state.projects.failed_attempts` | seat | <ui> 2 | - |
| `state.projects.paid_towards` | seat | <ui> 4, <engine-functions> 1 | - |
| `state.projects.stalled` | seat | seats 5 | seats 2 |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `active_projects` | table | yes | The seat's projects in progress (hours left, years, cost left), bounties, payments, failed attempts, stalls, exclusions. Replaces the forwarding property `active` and 49 direct UI reads. | - | `projects.active`, `projects.bountied`, `projects.paid_towards`, `projects.failed_attempts`, `projects.stalled`, `projects.excluded` | - | `active` | 11 |
| `project_cost` | quote | yes | What starting a project costs now: money, hours, materials; standing, reputation, opposition and money factors. | `project_cost`, `project_cost_now`, `opposition_factor`, `standing_floor`, `rep_factor`, `cost_money_factor` | - | `materials.project_materials`, `polity.standing`, `workforce.wage`, `mechanics.effect` | `done`, `active` | 7 |
| `committed_cost` | table | yes | Money still owed on work in hand. | `committed_spend` | - | `active_projects` | `active` | 2 |
| `start_check` | quote | yes | Whether a project can start and, if not, the first structured reason (cause plus facts), with the blockers a player sees. | `start_reason`, `can_start`, `start_refusal`, `start_blockers`, `_money_refusal`, `_visible_to_player`, `_missing_prereq_entries`, `_classify_check`, `exclusion_reason`, `exclusion_entry_known`, `bounty_eligible`, `substitution_quality` | - | `knowledge.techniques_held`, `knowledge.visibility`, `finance.spending_power`, `finance.debt_status`, `workforce.staffing_quote`, `production.running`, `resources.forest_and_nitre`, `living_stock.stock_status`, `polity.standing`, `diffusion.diffusion_index`, `mechanics.effect` | - | 6 |
| `project_risk` | quote | yes | Risk, precaution, calendar floor, payment schedule and the earliest and expected completion. | `effective_risk`, `precaution_quote`, `calendar_floor`, `payment_schedule_years`, `earliest_completion_years`, `expected_calendar_years` | - | `active_projects`, `hazards.hazard_figures`, `mechanics.effect` | `active` | 3 |
| `running_gates` | quote | yes | Running gates a technique still lacks, and what relies on a running capability. | `unmet_running_gates`, `ways_short`, `gate_blocked`, `running_gate_text`, `running_gate_refusal`, `relied_on_running`, `open_refusal`, `staffing_open_refusal` | - | `production.running`, `land.transport` | `operating` | 4 |
| `rebuild` | quote | yes | Whether a lost technique is being rebuilt and what survives. | `is_being_rebuilt`, `rebuild_survivals`, `rebuild_retained_share`, `rebuild_work_factor`, `rebuild_explanation` | - | `knowledge.techniques_held` | `done` | 3 |
| `outcome_quote` | quote | yes | Reputation gain, failure severity, goal closures and the opening shortfall for a project. | `reputation_gain_of`, `failure_severity`, `goal_closure_ids`, `goal_snapshot`, `goal_effect_lines`, `opening_shortfall` | - | `polity.standing` | - | 2 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `committed_cost`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 18 methods are referenced from other modules' mixin code: 14 are replaced by a view here, 4 by a command. 24 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 42 used names, 38 are covered by a view or command through the method itself, 4 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_money_refusal`, `effective_risk`, `expected_calendar_years`, `goal_effect_lines`, `goal_snapshot`, `open_refusal`, `opening_shortfall`, `project_cost`, `project_cost_now`, `staffing_open_refusal`, `start_blockers`, `start_refusal`, `substitution_quality`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `StartProject` | seat, node, via (own, bounty) | `initialize_project`, `start_project`, `begin_seat_project`: revalidates the same quote it was shown, then pays and registers. Methods: `_step_start_projects`, `_step_materials`, `start_project`, `begin_seat_project`, `initialize_project` | `sim/engine/projects_starting.py:69,250`, `sim/engine/step_phase_project_start.py` | `start_blocked (with the quote's cause)`, `cannot_afford`, `credit_frozen` | `projects.active`, `projects.paid_towards` |
| `StopProject` | seat, node, reason | `stop_project` and the places that pop `projects.active`. Methods: `stop_project` | `sim/engine/projects_starting.py:1041`, `sim/engine/step_phase_projects.py:113,256`, `sim/engine/credit_freeze.py:47`, `sim/engine/projects_completion.py:194` | `not_active` | `projects.active` |
| `PostBounty` | seat, node, price | `post_bounty`, `bribe`. Methods: `post_bounty`, `bribe` | `sim/engine/projects_starting.py:167,244` | `not_eligible` | `projects.bountied`, `household.bounties_paid` |
| `AdvanceProjects` | seat | `_step_progress`: hours drawn, money paid, completion or failure. Methods: `_step_progress` | `sim/engine/step_phase_projects.py:35-256` | none: always applies | `projects.active`, `projects.failed_attempts`, `projects.bountied` |
| `CloseLapsedDependents` | seat | `close_lapsed_dependents`: closes what relied on a capability that lapsed. Methods: `close_lapsed_dependents` | `sim/engine/projects_running_gates.py` | none: always applies | - |
| `LoseWhatWasRisked` | seat, node | `lose_what_was_risked`: a failed attempt takes staff and capital; assigns `employees[trade]` directly (`projects_completion.py:401-403`); sends LoseStaff and PayEdge. Methods: `lose_what_was_risked` | `sim/engine/projects_completion.py:401-403` | none: always applies | - |
| `ResetProgress` | seat, node, hours_left | Hazards that set a project back (written from outside today). | `sim/engine/society_hazards.py:562-563`, `sim/engine/projects_completion.py:309-345` | none: always applies | `projects.stalled` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `projects.active`: 6 sites: `sim/agents/household.py:345`, `sim/agents/household.py:231`, `sim/engine/society_hazards.py:562`, `sim/engine/society_hazards.py:563`, `sim/engine/credit_freeze.py:47` (.pop()), `sim/engine/core.py:599`
- `projects.bountied`: 1 site: `sim/engine/credit_freeze.py:52` (.discard())
- `projects.excluded`: 1 site: `sim/ui/proto/dispatch_exclusions.py:48` (.add())
- `projects.failed_attempts`: 1 site: `sim/agents/household.py:399`
- `projects.paid_towards`: 1 site: `sim/engine/credit_freeze.py:44`
- `projects.stalled`: 2 sites: `sim/engine/core_step_phases.py:578`, `sim/engine/core_step_phases.py:602`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `diffusion`: `diffusion.diffusion_index` (_is_foreign_only, civ_cost_factor, input of projects.start_check, needs_first)
- `finance`: `finance.credit_limit` (bearable_part_of, credit_limit); `finance.debt_status` (household.credit_frozen_until, household.insolvent_years, input of projects.start_check); `finance.spending_power` (funding_capacity, input of projects.start_check, spending_power)
- `hazards`: `hazards.hazard_figures` (input of projects.project_risk); `hazards.knowledge_risk` (_surviving_people, corpus_hedge)
- `knowledge`: `knowledge.techniques_held` (has, input of projects.rebuild, input of projects.start_check, projects.done ...); `knowledge.visibility` (fog, input of projects.start_check, is_visible, missing_prereq_message)
- `land`: `land.tile_facts` (geography, geography.material_cost_factor); `land.transport` (built_way_km, input of projects.running_gates)
- `ledger`: `ledger.acting_balance` (household.capital)
- `living_stock`: `living_stock.garrison` (venture_garrison); `living_stock.stock_status` (input of projects.start_check, stock_held)
- `materials`: `materials.generation` (generation_capacity_kw); `materials.material_demand` (CHARCOAL_PER_HA, annual_material_demand); `materials.project_materials` (bounty_price, failure_loss, input of projects.project_cost, project_cost_without_materials ...); `materials.resource_throttle` (holdings.binding, project_resource_throttle, resource_throttle)
- `mechanics`: `mechanics.capability_sets` (NOT_OPERATING_BENEFIT); `mechanics.effect` (effect_sum, input of projects.project_cost, input of projects.project_risk, input of projects.start_check); `mechanics.mechanic` (mechanic, nodes_with_mechanic); `mechanics.patronage` (approval_patron)
- `polity`: `polity.standing` (alarm_of, household.bribes_ytd, household.protection, household.reputation ...)
- `production`: `production.industry_depth` (after_failed_attempts, industry_depth, learn_from_failed_attempt); `production.revenue_estimate` (revenue); `production.running` (input of projects.running_gates, input of projects.start_check, is_venture, projects.operating ...); `production.upkeep` (upkeep)
- `reporting`: `reporting.event_log` (household.log)
- `resources`: `resources.forest_and_nitre` (holdings.forest_ha, input of projects.start_check, shortage_remedy); `resources.mine_cost` (MINE_OPEX_MATERIALS, _mine_capex, mine_operating_cost); `resources.mine_output` (holdings.mine_pending, mine_capacity)
- `seats`: `seats.founder` (founder.founder_alive, founder.policy, policy); `seats.goal` (_win_condition_value, goal)
- `ventures`: `ventures.closures` (projects.mothballed); `ventures.venture_crew` (venture_foreman, venture_foreman_free, venture_hands, venture_staff_free); `ventures.venture_quote` (opening_fee, reopen_fee, reopen_units)
- `workforce`: `workforce.hour_commitments` (household.hour_allocations, project_hour_pace, report_unused_directed_hours, trade_shortfall_note); `workforce.hours_available` (hour_priority_queue, labour.craft_hands_available, labour.director_hours_committed, labour.director_pool ...); `workforce.labour_market` (labour.market_supply); `workforce.living_cost` (living_cost); `workforce.staff` (household.artisans, household.employees, household.scholars, labour ...); `workforce.staffing_quote` (input of projects.start_check, labour.project_staffing_shortfall, labour.staff_advice); `workforce.wage` (input of projects.project_cost)

Sends (commands of other modules):

- `diffusion`: `ApplyTechEffects`
- `knowledge`: `LearnTechnique`, `RevealNodes`
- `ledger`: `NoteSpend`, `PayEdge`
- `living_stock`: `ChangeHeld`, `GrantStock`
- `materials`: `ApplyThrottle`
- `polity`: `ChangeStanding`, `PayState`
- `reporting`: `RecordEvent`
- `resources`: `BuyForest`, `OpenMine`, `Prospect`
- `seats`: `SetGoal`
- `ventures`: `CloseWork`
- `workforce`: `CommitHours`, `Hire`

Extension points it declares:

- start_checks (LIST): a function (view reader, seat, node) returning the first structured refusal or None; provided by living_stock (unheld stock), diffusion (foreign-only), knowledge (missing prerequisites, fog), finance (credit frozen, arrears), workforce (staff), polity (approval); replaces the `blocker_kind` registry in `sim/engine/blockers.py`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `seat_work`: `_step_start_projects`, `_step_progress` (`core_step_phases.py:125-139`)
- `money_seat`: `close_lapsed_dependents` (`step_phase_money.py:81`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 156 | `active`, `project_cost`, `start_reason`, `can_start`, `start_blockers`, `effective_risk`, `calendar_floor`, `start_refusal` |
| engine/(function modules) | 13 | `active`, `project_cost`, `effective_risk`, `rebuild_work_factor`, `begin_seat_project` |
| engine/ui* | 1 | `_visible_to_player` |
| engine/agents_port* | 1 | `effective_risk` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `active` 45 reads, `project_cost` 38, `start_reason` 10, `can_start` 10, `start_blockers` 5, `effective_risk` 4, `calendar_floor` 4, `expected_calendar_years` 3, `start_refusal` 3; agents_port: `effective_risk`.

## (h) Hard spots and caches

- `can_start` is a conjunction of about thirty `_check_*` rules, each reading a different module (credit, staff, fog, herd, stock, patron, win condition, scholar and craft staff): the heaviest reader in the engine and the plan's prototype 2.3. As a quote it reads about a dozen views (flag against the 15-read limit in MODULE_MIGRATION_TASKS.md 2.4).
- The year's start step interleaves checking and committing: each start changes cash, staff and hours, and the next candidate sees the result. `StartProject` must revalidate against live state, and a screen's `start_check` quote must agree with it (one function, two entry points).
- `projects.active` is written by hazards (`society_hazards.py:562`), credit freeze (`credit_freeze.py:47`) and read by sim/labour (`labour_staff_ledger.py:53`).
- `expected_calendar_years` is a quote that briefly sets `projects.failed_attempts[node]` to a trial value and puts it back (`projects_progress.py` around line 450): a rollback inside a read. The module must compute the same figure from a copy, and a test must show it equals the old value.
- `ActiveProjectState` objects are mutated in place through `projects.active[node]['yrs']` etc. (about 25 sites); the record must be owned and changed only by commands.

Caches and version counters held today (feed for task 1.2):

- `_goal_closure_by_goal` (`projects_completion.py:83`), `_dependents_index_cache` (`projects_rebuild.py:31`), `_running_gate_cache` (`projects_running_gates.py:73`)
- `active_version` counter and `_InvalidatingDict` on `projects.active` (`economy.py:243`)

Detected by the cache scan in this module's mixin files: `engine/economy.py:262 _annual_mat_demand_cache`, `engine/economy.py:270 _demand_by_tag_cache`, `engine/economy.py:221 _done_seq`, `engine/economy.py:265 _goods_cat_state_cache`, `engine/economy.py:266 _goods_category_ratios_cache`, `engine/economy.py:268 _goods_mkt_op_factor_cache`, `engine/economy.py:267 _income_factor_cache`, `engine/economy.py:269 _material_demand_cache`, `engine/economy.py:264 _practice_cache`, `engine/economy.py:263 _rev_up_candidates_cache`, `engine/economy.py:260 _revenue_cache_key`, `engine/economy.py:261 _revenue_cache_val`, `engine/projects_completion.py:83 __dict__[_goal_closure_by_goal]`, `engine/projects_rebuild.py:31 __dict__[_dependents_index_cache]` and 1 more.

## As built (task 2.3, `mr/project-start`)

What the first move of the start of a project changed in this draft, and why. Measured with `grep -c '^@bridge_view' sim/engine/bridge_projects.py` and the module's spec (`sim/projects/module_spec.py`).

- **Moved:** `StartingMixin`, `BlockersMixin`, `ProjectStartPhaseMixin`'s start step, `project_funding.py`, `SeatResearcher`, the pure rules the start path used (`start_money_rule`, `instantaneous_project`, `auto_start_rule`, `staff_gate`). `_step_materials` (woodland, mines, nitre beds) was in the same class and is not project starting: it stays in `step_phase_materials.py` for the resources topic. `OpenGateMixin`, `StaffingMixin` and its siblings, `VentureQuotesMixin` stay (they are `ventures`: opening, restoring and staffing a built work, not beginning a project); `RunningGatesMixin` stays because progress and the opening of a work use it, and the start test reads its check as a view.
- **Published (6):** `start_check`, `start_blockers`, `start_refusal`, `bounty_eligible` (quotes), `start_hours`, `last_start`. The draft's one `start_check` quote was three questions with three answer shapes (the first reason, the list of reasons, the text of the first), and its callers use all three, so it is three views. `substitution_quality`, `_money_refusal` and the `_check_*` rules are the module's own methods: nothing outside asks them.
- **Applied (4):** `StartProject`, `StopProject`, `PostBounty` and `Bribe` (the draft folded `bribe` into `PostBounty`; it is a different purchase). `AdvanceProjects`, `CloseLapsedDependents`, `LoseWhatWasRisked` and `ResetProgress` are progress and completion, not moved.
- **State:** the seat state holds `active`, `failed_attempts`, `bountied`, `paid_towards`, `bounties_paid` and `spend_last_year` beside the exclusions and the staffing records, all written by the module's own code and commands (`WatchActive` wraps `active` so that a change of any record moves `active_projects_version`). `stalled` is the seats module's (the dissolution count of a programme with no director); `done` and its kin are knowledge's; what is built, running and shut is ventures'. The project order is the module's own world state (`ProjectsWorld.order`), published as `project_order` and changed by `PutProjectFirst`, `ReorderProjects` and `RestoreProjectOrder`.
- **Reads (64, from 15 owners besides the module's own unmoved parts):** more than the draft's 42, because the draft named the owner's whole view and the module needs narrow questions (`visibility(node, memo)`, `hours_available[pool]`, `staff_advice(kind, deficit)`). Where the draft's grain fits it kept the catalogue name (`techniques_held`, `visibility`, `running`, `standing`, `credit_limit`, `project_cost`); where one catalogued view hid several unrelated questions it is several views here (`staffing_quote` became `project_staffing_shortfall`, `hours_available`, `trade_available`, `market_supply`, `staff_advice`, `training_advice`; `project_materials` became `own_output_claim`, `bounty_price`, `material_upfront_refusal`; `project_risk` became `calendar_floor` and `effective_risk`).
- **The start checks:** the table `START_CHECKS` (`sim/projects/blocker_rules.py`) is the order and the kind of every check; four of the 21 are answered by views of their owners (`start_gate_running`, `start_gate_unheld_stock`, `start_gate_material_seller`, `start_gate_group_prohibition`) until those owners publish their checks. A mod adds a check by providing to the extension point `extra_start_checks` (asked after the shipped ones) and removes or reorders one by a layer over `START_CHECKS`.
- **Not in the draft, needed:** a view of the year (`year`), of presentation (`money_text`), of the run's settings (`automation`: manual play and the bounty list), and of the acting seat. None has an owner in the catalogue.
