# Module `ventures`

Concerns the seat opens and closes: crews, foremen, staffing closures, quotes and auto-opening.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 4 / 3 |
| Old methods and properties owned (after regrouping) | 59 |
| Of those, referenced from another module's mixin code | 19 (7 classed read-only or pure by Appendix B, 12 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 33 (19 from mixins, 14 only from outside) |
| Views per used name | 0.12 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 4 |
| Views of other modules it reads | 24, from 12 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 4 |

**Existing surface and files.** Engine: `VenturesMixin`, `VentureQuotesMixin`, `StaffingMixin` (21), `StaffingShortfallMixin`, `StaffingReportMixin`; function modules `staff_gate.py`, `staffing_choice.py`, `staffing_events.py`, `closure_grace.py`, `venture_net_loss.py`, `projects_review.py`, `payroll_trim.py`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `VenturesMixin` | `sim/engine/projects_ventures.py` | 16 | 8 |
| `StaffingMixin` | `sim/engine/projects_staffing.py` | 21 | 7 |
| `StaffingShortfallMixin` | `sim/engine/projects_staffing_shortfall.py` | 7 | 0 |
| `StaffingReportMixin` | `sim/engine/projects_staffing_report.py` | 6 | 0 |
| `VentureQuotesMixin` | `sim/engine/projects_venture_quotes.py` | 7 | 4 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 3 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_auto_expand_institutions`, `_auto_open_check_deep_arrears`, `_auto_open_institution_budget`, `_auto_open_institution_candidates`, `_auto_open_institutions`, `_auto_open_log_blocked`, `_auto_open_ordinary_candidates`, `_auto_open_ordinary_ventures`, `_expand_institution`, `_staffing_allowances`, `_staffing_draw_of`, `_staffing_draws`, `_staffing_shortfalls`, `_staffing_tally`, `clear_closure`, `close_venture`, `closure_of`, `crew_figures`, `mothballed`, `record_staffing_closures`, `record_staffing_reopenings`, `shut_for_staff`, `staffing_shortfall_words`, `staffing_shut_count`, `venture_crew_by_trade`, `venture_foremen_used`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `VenturesSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.projects.businesses` | seat | - | - |
| `state.projects.closures` | seat | hazards 2 | - |
| `state.projects.ever_closed_for_staff` | seat | <ui> 1 | - |
| `state.projects.keep_staffed` | seat | <ui> 4 | <ui> 2 |
| `state.projects.mothballed` | seat | projects 3, hazards 1 | projects 1, hazards 1 |
| `state.projects.staffing_tally` | seat | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `venture_crew` | keyed | yes | Hands, foremen and staff a venture needs, uses and has free, by trade. | `venture_hands`, `venture_hands_founder_staffed`, `venture_crew_by_trade`, `concern_staff_by_trade`, `crew_figures`, `venture_foreman`, `venture_foremen_used`, `venture_foreman_free`, `venture_staff_used`, `venture_staff_free`, `venture_staff_who_is_watching_what` | - | `workforce.staff`, `production.running` | `operating`, `workforce` | 5 |
| `venture_quote` | quote | yes | A venture's real earnings and upkeep, forecast and sale basis, opening and reopening fees, capex. | `venture_real_earnings`, `venture_real_upkeep`, `venture_upkeep_quote`, `venture_forecast_basis`, `venture_sale_basis`, `opening_fee`, `reopen_units`, `reopen_fee`, `venture_capex` | - | `production.revenue_estimate`, `production.upkeep`, `prices.material_prices`, `venture_crew` | `operating` | 3 |
| `closures` | table | yes | Ventures closed for staff and why; warnings, ages, shortfall words, counts. | `closure_of`, `staff_closure_age`, `staffing_closure_warnings`, `staffing_shut_count`, `staffing_shortfall_words`, `staffing_closure_summary`, `staffing_missing_to_open`, `concerns_to_close_for_staffing`, `review_ventures`, `note_venture_year` | `projects.closures`, `projects.mothballed`, `projects.keep_staffed`, `projects.ever_closed_for_staff`, `projects.staffing_tally`, `projects.businesses` | `venture_crew` | `operating`, `workforce` | 6 |
| `staffing_shortfalls` | quote | yes | What each concern lacks in staff and what it may draw. | `_staffing_shortfalls`, `staffing_held_totals`, `_staffing_allowances`, `_staffing_draws`, `staffing_closed_hand_shortfall` | - | `workforce.staff`, `production.running` | `workforce` | 2 |

**Coverage.** 19 methods are referenced from other modules' mixin code: 14 are replaced by a view here, 5 by a command. 14 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 33 used names, 33 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_staffing_draws`, `concern_staff_by_trade`, `concerns_to_close_for_staffing`, `opening_fee`, `reopen_fee`, `staffing_closed_hand_shortfall`, `staffing_closure_summary`, `staffing_closure_warnings`, `staffing_held_totals`, `staffing_missing_to_open`, `venture_capex`, `venture_forecast_basis`, `venture_hands`, `venture_real_earnings`, `venture_sale_basis`, `venture_staff_free`, `venture_staff_used`, `venture_staff_who_is_watching_what`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `OpenVenture` | seat, node, scale | `open_venture`, `_expand_institution`, `auto_open_ventures`. Methods: `open_venture`, `auto_open_ventures` | `sim/engine/projects_ventures.py:252,323`, `sim/engine/projects_staffing.py (auto_open_*)` | `cannot_afford`, `no_staff`, `gate_blocked` | `projects.businesses` |
| `CloseWork` | seat, node, reason | `close_work`, `close_venture`, `close_unstaffed_ventures`, `mothball_work`, `restore_work`, `reopen_restaffed_ventures`. Methods: `close_work`, `close_unstaffed_ventures`, `reopen_restaffed_ventures`, `mothball_work`, `restore_work` | `sim/engine/projects_staffing.py:751`, `sim/engine/society_hazards.py (mothballed)` | `not_running` | `projects.closures`, `projects.mothballed`, `projects.ever_closed_for_staff`, `projects.staffing_tally` |
| `KeepStaffed` | seat, node, flag | The player's flag keeping a concern staffed (written from sim/ui). | `sim/ui/proto/dispatch_ventures.py` | none: always applies | `projects.keep_staffed` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `projects.keep_staffed`: 2 sites: `sim/ui/proto/dispatch_staff_controls.py:32` (.add()), `sim/ui/proto/dispatch_staff_controls.py:34` (.discard())
- `projects.mothballed`: 2 sites: `sim/engine/society_hazards.py:608` (.discard()), `sim/engine/projects_starting.py:993` (.discard())

## (e) Reads and sends

Reads (views of other modules), by provider:

- `diffusion`: `diffusion.staff_advice` (STAFF_SOURCES)
- `finance`: `finance.credit_limit` (credit_limit); `finance.spending_power` (spending_power)
- `knowledge`: `knowledge.techniques_held` (projects.done, projects.granted); `knowledge.visibility` (never_abandon)
- `ledger`: `ledger.acting_balance` (household.capital)
- `living_stock`: `living_stock.garrison` (venture_garrison)
- `mechanics`: `mechanics.capability_sets` (CAPABILITY_INSTITUTIONS, SCALABLE_INSTITUTIONS)
- `prices`: `prices.material_prices` (input of ventures.venture_quote)
- `production`: `production.concern_market` (concern_goods_have_market, concern_sale_basis, concern_takings, node_output_market_factor); `production.industry_depth` (concern_runs_without_founder); `production.institution_units` (institution_unit_ceiling, institution_unit_cost, institution_units); `production.revenue_estimate` (input of ventures.venture_quote, revenue, venture_ramp); `production.running` (_practisable, input of ventures.staffing_shortfalls, input of ventures.venture_crew, is_venture ...); `production.upkeep` (input of ventures.venture_quote, institution_places, institution_upkeep, upkeep)
- `projects`: `projects.project_cost` (project_cost); `projects.running_gates` (open_refusal, running_gate_refusal); `projects.start_check` (exclusion_reason)
- `reporting`: `reporting.event_log` (household.log)
- `seats`: `seats.founder` (founder.founder_alive)
- `workforce`: `workforce.literacy_capacity` (labour.effective_scholars); `workforce.living_cost` (HOURS_PER_PERSON_YEAR, living_cost); `workforce.staff` (household.artisans, household.employees, household.scholars, input of ventures.staffing_shortfalls ...); `workforce.wage` (labour.yearly_value_of)

Sends (commands of other modules):

- `knowledge`: `LearnTechnique`
- `ledger`: `PayEdge`
- `projects`: `CloseLapsedDependents`
- `reporting`: `RecordEvent`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `money_seat`: `reopen_restaffed_ventures`, `close_unstaffed_ventures`, `auto_open_ventures`, `note_venture_year` (`step_phase_money.py:75-94`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 67 | `venture_real_earnings`, `venture_real_upkeep`, `venture_upkeep_quote`, `opening_fee`, `venture_forecast_basis`, `venture_sale_basis`, `venture_hands`, `venture_foreman` |
| engine/(function modules) | 3 | `concerns_to_close_for_staffing`, `open_venture`, `close_work` |
| labour | 1 | `concerns_to_close_for_staffing` |
| engine/agents_port* | 1 | `concern_staff_by_trade` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `venture_real_earnings` 16, `venture_real_upkeep` 10, `venture_upkeep_quote` 10, `opening_fee` 4, `venture_forecast_basis` 3, `venture_sale_basis` 3, `venture_hands` 3; sim/labour: `concerns_to_close_for_staffing`.

## (h) Hard spots and caches

- Staffing closures run inside the money and staff steps and call back into production and finance (`review_ventures` 2 calls from finance); the order close -> reopen -> auto-open is fixed.
- `venture_real_earnings` is called 16 times by the UI, each a revenue computation: cost depends on the shared revenue cache.

Caches and version counters held today (feed for task 1.2):

- none of its own; relies on `operating_version`, `workforce_version`
