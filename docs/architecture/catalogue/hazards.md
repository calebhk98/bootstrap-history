# Module `hazards`

Disasters and shocks: random events, dated shocks, world hazards, famine watch, relief and the output factor.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 4 / 2 |
| Old methods and properties owned (after regrouping) | 52 |
| Of those, referenced from another module's mixin code | 8 (3 classed read-only or pure by Appendix B, 5 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 16 (8 from mixins, 8 only from outside) |
| Views per used name | 0.25 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 4 |
| Views of other modules it reads | 25, from 14 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 12 |

**Existing surface and files.** Existing: `sim/world/` hazard data (`world_hazard_data.py`, `hazard_condition.py`, `hazard_window.py`, `hazard_toll.py`, `hazard_merge.py`). Engine: `HazardsMixin` (21), `HazardReliefMixin` (12), `WorldHazardsMixin`, `ShockYearMixin` (11), `_step_dated_shocks`, `Fog._epidemic_risk/knowledge_risk`, `Sim.corpus_hedge`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `Sim` | `sim/engine/core.py` | 1 | 1 |
| `FogMixin` | `sim/engine/fog.py` | 2 | 0 |
| `ShockYearMixin` | `sim/engine/shock_year.py` | 11 | 0 |
| `HazardReliefMixin` | `sim/engine/hazard_relief.py` | 12 | 2 |
| `HazardsMixin` | `sim/engine/society_hazards.py` | 21 | 4 |
| `WorldHazardsMixin` | `sim/engine/world_hazards.py` | 3 | 0 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 2 | 2 |
| `StepPhasesMixin` | `sim/engine/core_step_phases.py` | 1 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_apply_event_causes`, `_calendar_floor_remaining`, `_closure_words`, `_counter_requirements`, `_counter_strength`, `_entry_words`, `_epidemic_risk`, `_log_corpus_loss`, `_loss_words`, `_military_war_relief`, `_national_sources_words`, `_random_events_for_seat`, `_resolve_hazard_condition`, `_sack_corpus_loss`, `_sack_site`, `_shock_output_factor`, `_shock_output_factor_seats`, `_shock_real_erosion`, `_shock_real_erosion_seats`, `_shock_sack_chance`, `_shock_staff_loss`, `_shock_staff_loss_seats`, `_shock_values`, `_shock_values_seats`, `_shocks`, `_staff_loss_message`, `_staff_loss_of_seat`, `_yr_words`, `hazard_advice`, `hazard_relief_detail`, `hazard_timeline`, `hedge_first_steps`, `mitigation_table`, `national_public_health_sources`, `output_floor`, `staff_loss_exposure`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `HazardsWorld`, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.output_factor` | world | production 7, finance 2, <agents> 2, markets 1, polity 1 | core 1, finance 1 |
| `state.economy.world_events` | world | <engine-functions> 3 | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `hazard_figures` | keyed | yes | Annual chance, toll and counter of a hazard; advice, hedge steps, timeline, mitigation table and effect preview. | `hazard_figure`, `hazard_effect_preview`, `hazard_advice`, `hedge_first_steps`, `hazard_timeline`, `_calendar_floor_remaining`, `_counter_strength`, `_counter_requirements`, `mitigation_table`, `output_floor`, `staff_loss_exposure` | `economy.world_events` | `mechanics.corpus`, `knowledge.techniques_held`, `production.running`, `workforce.staff` | `hazards` | 3 |
| `hazard_relief` | table | yes | Relief entries and detail: what each held technique takes off a hazard; public health sources. | `hazard_relief_entries`, `hazard_relief`, `hazard_relief_detail`, `national_public_health_sources` | - | `mechanics.effect`, `production.running`, `diffusion.diffusion_relief` | `hazards` | 2 |
| `knowledge_risk` | quote | yes | The risk of losing knowledge (staff, epidemic, corpus hedge). | `knowledge_risk`, `_epidemic_risk`, `corpus_hedge`, `_surviving_people` | - | `mechanics.corpus`, `disease.epidemic_forecast` | - | 3 |
| `output_factor` | table | no | The year's multiplier on output from shocks (read by revenue, credit, markets). | `output_factor` | `economy.output_factor` | - | `shocks` | 6 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `hazard_relief`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 8 methods are referenced from other modules' mixin code: 5 are replaced by a view here, 3 by a command. 8 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 16 used names, 12 are covered by a view or command through the method itself, 0 through a field alias, 4 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `hazard_advice`, `hazard_effect_preview`, `hazard_figure`, `hazard_relief`, `hazard_relief_detail`, `hazard_relief_entries`, `hazard_timeline`, `hedge_first_steps`, `knowledge_risk`, `mitigation_table`, `staff_loss_exposure`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `RunRandomEvents` | year, seats | `_random_events`, `_catastrophe`, `_resolve_hazard_condition`: draws in a fixed order and sends losses to owners. Methods: `_catastrophe`, `lose_capital`, `apply_staff_survival`, `_random_events` | `sim/engine/year_phases.py:_random_events`, `sim/engine/society_hazards.py` | none: always applies | `economy.world_events` |
| `SetOutputFactor` | factor | `_shock_output_factor`, `_shock_output_factor_seats`, money-phase decay. | `sim/engine/shock_year.py:134`, `sim/engine/step_phase_money.py:175`, `sim/engine/core.py:507` | none: always applies | `economy.output_factor` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `economy.output_factor`: 2 sites: `sim/engine/step_phase_money.py:175`, `sim/engine/core.py:507` (assign (alias))

## (e) Reads and sends

Reads (views of other modules), by provider:

- `diffusion`: `diffusion.diffusion_index` (_diffusible_ids, civ_diffusion); `diffusion.diffusion_relief` (_state_military_diffusion_relief, input of hazards.hazard_relief, medical_diffusion_relief)
- `disease`: `disease.epidemic_forecast` (epidemic_forecast, input of hazards.knowledge_risk)
- `knowledge`: `knowledge.techniques_held` (has, input of hazards.hazard_figures, projects.done, projects.forgotten ...); `knowledge.visibility` (fog, is_visible)
- `ledger`: `ledger.acting_balance` (household.capital)
- `living_stock`: `living_stock.garrison` (counter_supply_gap)
- `mechanics`: `mechanics.capability_sets` (HAZARD_COUNTERS); `mechanics.corpus` (best_corpus_node, corpus_hedge_tiers, input of hazards.hazard_figures, input of hazards.knowledge_risk ...); `mechanics.effect` (input of hazards.hazard_relief); `mechanics.mechanic` (nodes_with_mechanic)
- `polity`: `polity.standing` (household.protection, household.scandal_last_year); `polity.state_treasury` (military_leverage)
- `production`: `production.running` (capability_gaps, input of hazards.hazard_figures, input of hazards.hazard_relief, projects.operating ...)
- `projects`: `projects.active_projects` (projects.active); `projects.project_cost` (project_cost); `projects.start_check` (start_reason)
- `reporting`: `reporting.event_log` (household.log, log)
- `resources`: `resources.mine_output` (mine_capacity)
- `seats`: `seats.founder` (founder.last_patron_death, founder.policy, policy); `seats.goal` (goal); `seats.seat_list` (playing_seats)
- `ventures`: `ventures.closures` (projects.closures, projects.mothballed)
- `workforce`: `workforce.staff` (household.artisans, household.employees, household.scholars, input of hazards.hazard_figures ...); `workforce.wage_index` (wage_index)

Sends (commands of other modules):

- `coin`: `ChargeTheft`
- `demography`: `KillPeople`
- `knowledge`: `LearnTechnique`
- `ledger`: `PayEdge`
- `polity`: `ChangeStanding`
- `production`: `SetOperating`
- `projects`: `StartProject`
- `reporting`: `RecordEvent`
- `seats`: `FounderDies`
- `ventures`: `CloseWork`
- `workforce`: `Fire`, `Hire`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `dated_shocks`
- `random_events`
- `world_hazards`
- `money_world`: the output-factor decay (`step_phase_money.py:175-176`)
- `famine_watch`

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 10 | `hazard_figure`, `knowledge_risk`, `hazard_relief_entries`, `hazard_effect_preview`, `hazard_relief` |
| engine/(function modules) | 7 | `_random_events`, `_step_dated_shocks`, `step_world_hazards`, `step_famine_watch`, `check_yearly_world`, `lose_capital`, `knowledge_risk` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `hazard_figure` 3, `knowledge_risk` 3, `hazard_relief_entries` 2, `hazard_effect_preview`, `hazard_relief`; engine: `_random_events`, `step_world_hazards`, `step_famine_watch`, `lose_capital`.

## (h) Hard spots and caches

- Hazards today write directly into eight other modules' fields (`society_hazards.py`: artisans, employees, scholars, directors_extra, projects.active/done/mothballed/operating, founder.last_patron_death, protection, scandal, dead_reason): each becomes a command (LoseStaff, ForgetTechnique, SetOperating, CloseWork, ResetProgress, ChangeStanding, FounderDies, ChargeTheft). This is the single biggest writer fan-out.
- Random draws must keep their order: `_random_events` iterates seats under `act_as`; the command sequence per event must match the old write sequence or the stream diverges (equivalence tool, random state).
- `hazard_figures` for the UI previews effects without applying them; same pure-quote versus commit split as materials.

Caches and version counters held today (feed for task 1.2):

- none of its own
