# Module `polity`

The state and the household's standing with it: reputation, scandal, eminence, protection, levies, reach, interest groups.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 7 / 4 |
| Old methods and properties owned (after regrouping) | 58 |
| Of those, referenced from another module's mixin code | 13 (10 classed read-only or pure by Appendix B, 3 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 32 (13 from mixins, 19 only from outside) |
| Views per used name | 0.22 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 7 |
| Views of other modules it reads | 25, from 14 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 9 |

**Existing surface and files.** Existing: `sim/agents/government*.py`, `authority.py`, `unrest.py`, `taxpayer_income.py`, `patronage.py` (state-side actors). Engine: `StatePressureMixin` (22 methods; `society_state_pressure.py` is over 1,300 lines), `LegitimacyMixin`, `InterestGroupsMixin`, `TransfersMixin`, `ConcernLevyMixin`, `BenefactionsMixin` and `SocietyMixin` (both empty shells), the state methods of `ActorsMixin`, `_step_reputation`; function modules `state_demand.py`, `state_notice_rules.py`, `eminence_rules.py`, `eminence_warning.py`, `military_rules.py`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `ProductionMixin` | `sim/engine/economy_production.py` | 3 | 0 |
| `StatePressureMixin` | `sim/engine/society_state_pressure.py` | 22 | 5 |
| `ActorsMixin` | `sim/engine/society_actors.py` | 4 | 1 |
| `InterestGroupsMixin` | `sim/engine/interest_groups.py` | 7 | 0 |
| `TransfersMixin` | `sim/engine/transfers.py` | 6 | 1 |
| `ConcernLevyMixin` | `sim/engine/concern_levy.py` | 2 | 0 |
| `LegitimacyMixin` | `sim/engine/legitimacy.py` | 7 | 4 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 12 | 4 |
| `StepPhasesMixin` | `sim/engine/core_step_phases.py` | 1 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_banned_materials`, `_group_records`, `_notice_over`, `_staff_reach`, `_state_pressure`, `_step_reputation`, `_technique_bans`, `concern_levy_due`, `confiscation_risk`, `group_levy_reasons`, `group_prohibition_of`, `military_demand_eligible`, `office_report`, `patron_clients`, `patron_funding_ask`, `pay_concern_levies`, `pay_state`, `pay_state_sum`, `prominence_hazard`, `requisition_report`, `state_claims`, `state_funding`, `state_legitimacy`, `state_levy_rates`, `state_military_ask`, `transfer_size`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `PolitySeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.governance.gov` | seat | - | projects 1 |
| `state.household.atrocity` | seat | - | - |
| `state.household.bribes_ytd` | seat | projects 4 | projects 1 |
| `state.household.concealed` | seat | <engine-functions> 3 | <engine-functions> 1 |
| `state.household.defiance` | seat | <engine-functions> 4 | <engine-functions> 2 |
| `state.household.demand_stance` | seat | <engine-functions> 3, <ui> 2 | <engine-functions> 1 |
| `state.household.eminence` | seat | <ui> 3, coin 1, <engine-functions> 1 | - |
| `state.household.familiarity` | seat | <ui> 1 | - |
| `state.household.last_military_demand` | seat | - | - |
| `state.household.last_withdrawal` | seat | - | - |
| `state.household.protection` | seat | projects 5, hazards 3, <engine-functions> 3, coin 2, <ui> 2 | hazards 1 |
| `state.household.reputation` | seat | <ui> 6, finance 5, projects 3, production 1, diffusion 1 | finance 3, <engine-functions> 2, projects 1, diffusion 1 |
| `state.household.scandal` | seat | <ui> 7, projects 5, core 1 | <engine-functions> 3, projects 2, hazards 1, living_stock 1 |
| `state.household.scandal_last_year` | seat | hazards 1, living_stock 1, <ui> 1 | core 1, hazards 1, living_stock 1 |
| `state.household.service_offer` | seat | <engine-functions> 2 | <engine-functions> 1 |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `standing` | table | yes | The seat's reputation, scandal (this and last year), eminence, familiarity, protection, demand stance, concealment; the state's interest, alarm, notice and the confiscation risk and status. Replaces forwarding properties `reputation`, `scandal`, `scandal_last_year`, `protection`, `eminence`. | `scandal`, `scandal_last_year`, `state_interest`, `alarm_of`, `state_notice`, `notice_over`, `_notice_over`, `eminence_report`, `prominence_hazard`, `confiscation_risk`, `confiscation_status`, `state_pressure_report`, `state_trait_weights` | `household.reputation`, `household.scandal`, `household.scandal_last_year`, `household.eminence`, `household.familiarity`, `household.protection`, `household.demand_stance`, `household.service_offer`, `household.concealed`, `household.defiance`, `household.bribes_ytd`, `household.atrocity` | `actors.cast`, `mechanics.effect` | `standing` | 14 |
| `visible_scale` | quote | yes | How visible a holder's wealth is to the state. | `visible_scale`, `household_scale` | - | `ledger.balance`, `standing` | - | 5 |
| `patronage_funding` | quote | yes | What the state and patrons fund, and the clients a patron has. | `patron_funding_ask`, `patron_clients` | - | `actors.cast` | `state` | 0 |
| `state_reach` | keyed | no | How far the state's order, inspection, forest rules and authority reach. | `state_reach`, `order_reach`, `inspection_reach`, `forest_reach`, `state_authority`, `state_legitimacy`, `_staff_reach` | - | `actors.cast`, `workforce.staff`, `demography.population` | `state` | 9 |
| `state_treasury` | table | yes | The state's treasury and its asks: levy rates, military ask and leverage, equipment burden, requisition and office reports, levy shares, eligibility. | `state_treasury`, `state_levy_rates`, `state_military_ask`, `military_leverage`, `military_equipment_burden_kg_per_soldier_per_year`, `levy_shares`, `requisition_report`, `office_report`, `military_demand_eligible`, `concern_levy_due`, `state_funding` | `governance.gov` | `actors.cast`, `standing` | `state` | 9 |
| `state_account` | table | yes | What the seat owes the state and what the state owes the seat; the size of a transfer. | `state_debt`, `state_claims`, `transfer_size` | - | `ledger.acting_balance` | `state` | 1 |
| `interest_groups` | table | no | Interest groups, their levies, bans and what a group prohibits. | `interest_groups`, `interest_groups_report`, `group_levy_reasons`, `group_prohibition_of`, `_banned_materials`, `_technique_bans`, `_group_records` | - | `actors.cast` | `groups` | 1 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `state_account`, `interest_groups`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 13 methods are referenced from other modules' mixin code: 11 are replaced by a view here, 2 by a command. 19 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 32 used names, 28 are covered by a view or command through the method itself, 4 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `concern_levy_due`, `patron_clients`, `state_funding`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `ChangeStanding` | seat, deltas (reputation, scandal, eminence, protection, ...) | Direct writes to the household's standing fields from many modules. | `sim/engine/economy_credit.py (reputation)`, `sim/engine/projects_completion.py (reputation, scandal)`, `sim/engine/society_disclosure.py (reputation)`, `sim/engine/society_hazards.py (protection, scandal)`, `sim/engine/projects_starting.py (bribes_ytd, scandal)`, `sim/engine/living_stock_smuggling.py (scandal)`, `sim/engine/core_step_phases.py (reputation, eminence, familiarity)` | none: always applies | `household.reputation`, `household.scandal`, `household.scandal_last_year`, `household.eminence`, `household.familiarity`, `household.protection`, `household.bribes_ytd`, `household.demand_stance`, `household.service_offer`, `household.concealed`, `household.defiance`, `household.last_withdrawal`, `household.last_military_demand`, `household.atrocity`, `governance.gov` |
| `RunStatePressure` | year | `_state_pressure`: the yearly step that sets protection, last military demand and withdrawal; the report builders only read what it left. Methods: `_state_pressure` | `sim/engine/society_state_pressure.py (_state_pressure)` | none: always applies | - |
| `PayState` | seat, amount, purpose | `pay_state`: a levy, office or requisition, then sends PayEdge to the ledger. Methods: `pay_state`, `carry_out_transfers`, `update_protection` | `sim/engine/society_state_pressure.py:1218,1265`, `sim/engine/concern_levy.py:30`, `sim/engine/transfers.py:40` | `unknown_government` | - |
| `SettleWithState` | seat, kind | `settle_with_state`, `withdraw_from_public_life`. Methods: `settle_with_state`, `withdraw_from_public_life` | `sim/ui/proto/ (settle_with_state 2)` | `nothing_owed` | - |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `governance.gov`: 1 site: `sim/engine/projects_completion.py:224`
- `household.bribes_ytd`: 3 sites: `sim/engine/core_step_phases.py:461`, `sim/engine/core_step_phases.py:465`, `sim/engine/projects_starting.py:168`
- `household.concealed`: 2 sites: `sim/agents/household.py:307`, `sim/engine/state_demand.py:82`
- `household.defiance`: 3 sites: `sim/agents/household.py:310`, `sim/engine/state_demand.py:28`, `sim/engine/state_demand.py:84`
- `household.demand_stance`: 1 site: `sim/engine/state_demand.py:112`
- `household.eminence`: 3 sites: `sim/engine/core_step_phases.py:453`, `sim/engine/core_step_phases.py:511`, `sim/engine/core_step_phases.py:520`
- `household.familiarity`: 2 sites: `sim/labour/labour_settlement.py:201`, `sim/engine/core_step_phases.py:381`
- `household.protection`: 2 sites: `sim/labour/labour_settlement.py:202`, `sim/engine/society_hazards.py:748`
- `household.reputation`: 11 sites: `sim/labour/labour_bondage.py:359`, `sim/engine/society_disclosure.py:46`, `sim/engine/core_step_phases.py:376`, `sim/engine/core_step_phases.py:504`, `sim/engine/core_step_phases.py:521`, `sim/engine/state.py:177` (assign (alias)), `sim/engine/state.py:181` (assign (alias)), `sim/engine/projects_completion.py:221`, `sim/engine/economy_credit.py:523`, `sim/engine/economy_credit.py:525` and 1 more
- `household.scandal`: 10 sites: `sim/engine/living_stock_smuggling.py:122` (assign (alias)), `sim/engine/society_hazards.py:743`, `sim/engine/core_step_phases.py:448`, `sim/engine/core_step_phases.py:466`, `sim/engine/core_step_phases.py:462`, `sim/engine/projects_starting.py:169`, `sim/engine/state.py:185` (assign (alias)), `sim/engine/agents_port_groups.py:147`, `sim/engine/state_demand.py:29`, `sim/engine/projects_completion.py:223`
- `household.scandal_last_year`: 3 sites: `sim/engine/living_stock_smuggling.py:124` (assign (alias)), `sim/engine/society_hazards.py:746`, `sim/engine/core_step_phases.py:114`
- `household.service_offer`: 1 site: `sim/engine/state_demand.py:113`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.ensure_government, actors.government_of, actors.home_actors ...)
- `coin`: `coin.coin_carriage` (coin_carriage_listening)
- `demography`: `demography.population` (input of polity.state_reach, pop_scale)
- `hazards`: `hazards.output_factor` (economy.output_factor)
- `knowledge`: `knowledge.techniques_held` (projects.done, projects.granted)
- `ledger`: `ledger.acting_balance` (household.capital, input of polity.state_account); `ledger.balance` (input of polity.visible_scale)
- `markets`: `markets.agent_economy` (holdings.market_pressure)
- `materials`: `materials.material_pool` (_material_tag)
- `mechanics`: `mechanics.effect` (effect_best, effect_factor, effect_sum, effect_values ...); `mechanics.mechanic` (mechanic, nodes_with_mechanic); `mechanics.patronage` (patrons_lost_to_eminence)
- `production`: `production.revenue_estimate` (concern_revenue, revenue); `production.running` (projects.operating, running, running_with_mechanic)
- `projects`: `projects.project_cost` (rep_factor, standing_floor)
- `reporting`: `reporting.event_log` (household.log, seat_progress._said_scandal); `reporting.real_output` (real_output_per_head)
- `seats`: `seats.acting_seat` (acting_country); `seats.founder` (founder.founder_alive, founder.policy); `seats.seat_list` (playing_seats)
- `workforce`: `workforce.hour_commitments` (hours_this_year, household.relocation_hours_this_year, household.supervision_hours_this_year, household.teaching_hours_this_year ...); `workforce.hours_available` (labour.director_pool); `workforce.labour_market` (labour.STATE_WEIGHTS, labour.money_per_labour_hour); `workforce.staff` (input of polity.state_reach, labour, labour.headcount); `workforce.wage` (labour.base_annual_wage)

Sends (commands of other modules):

- `hazards`: `RunRandomEvents`
- `knowledge`: `LearnTechnique`
- `ledger`: `NoteSpend`, `PayEdge`
- `markets`: `ClearYear`
- `reporting`: `NoteOnce`, `RecordEvent`
- `workforce`: `CommitHours`, `NotePay`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `begin_seat_year`: the scandal mark (`core_step_phases.py:110-116`)
- `seat_work`: the polity part of `_step_reputation` (`update_protection`, `pay_concern_levies`, `core_step_phases.py:375-447`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 34 | `scandal`, `reputation`, `eminence`, `eminence_report`, `settle_with_state`, `protection`, `state_notice`, `state_reach` |
| engine/(function modules) | 13 | `state_treasury`, `state_reach`, `state_interest`, `visible_scale` |
| agents | 11 | `state_reach`, `notice_over`, `levy_shares` |
| engine/agents_port* | 8 | `military_equipment_burden_kg_per_soldier_per_year`, `state_authority`, `notice_over`, `state_trait_weights`, `visible_scale`, `levy_shares`, `state_treasury` |
| engine/economy_port* | 2 | `state_reach`, `state_treasury` |
| mods | 2 | `visible_scale`, `confiscation_status` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `scandal` 7, `reputation` 6, `eminence` 3, `eminence_report` 2, `settle_with_state` 2; sim/agents: `state_reach` 7, `notice_over` 3, `levy_shares`; agents_port: `military_equipment_burden_kg_per_soldier_per_year` 2, `state_authority`, `state_trait_weights`; mods: `visible_scale`, `confiscation_status`.

## (h) Hard spots and caches

- `StatePressureMixin` is the largest single class (22 methods, about 1,300 lines of one file); it reads `household.*`, `value_weights`, `cfg`, and the state's records, and writes protection, withdrawal, military demand and reputation: split into standing (household-side), the state's asks (government-side) and the report builders (reporting).
- `state_reach` and `_staff_reach` cache per year by key (`legitimacy.py:44,64`).
- `_step_reputation` (`core_step_phases.py:368-420`) writes three owners' fields: reputation, familiarity and protection (this module), the hour tallies and `hours_this_year` (workforce) and `spend_last_year` (ledger); only the first part stays here.
- Several writes to `scandal` happen through the forwarding property setter (`self.scandal =`), so the write site is invisible to a field grep; list them by the property name.

Caches and version counters held today (feed for task 1.2):

- `_state_reach_memo`, `_staff_reach_memo` (`legitimacy.py:44,64`), `_banned_materials_cache` (`interest_groups.py:80`)

Detected by the cache scan in this module's mixin files: `engine/interest_groups.py:80 __dict__[_banned_materials_cache]`, `engine/legitimacy.py:64 __dict__[_staff_reach_memo]`, `engine/legitimacy.py:44 __dict__[_state_reach_memo]`.
