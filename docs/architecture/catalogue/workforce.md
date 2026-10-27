# Module `workforce`

People who work: staff by trade, hours, wages, training, slaves and the labour market.

**Status:** partly moved, on branch `mr/workforce` (package `sim/workforce/`, bridge `sim/engine/bridge_workforce.py`, forwarders
`sim/engine/forward_workforce.py`). The tables below are the draft of task 1.5 (a read-only analysis of `e8b004c`); "What the move
built" says what shipped and what did not. Re-measure with `python3 -c "import sys; sys.path.insert(0,'.'); from sim.workforce import
module_spec as m; s=m.MODULE_SPECS[0]; print(len(s.publishes), len(s.applies), len(s.reads), len(s.sends), len(s.phases))"`.

## What the move built

The module holds `Labour` (`sim/labour/`, unchanged inside) and builds it over `WorkforceWorld` (`sim/workforce/world.py`), which
answers each of the 100-odd things labour reads of the game from a view the spec declares. `LabourWorld` and `LabourPortMixin`
(`sim/engine/labour_port.py`) are gone; `Sim.labour` is a property in `forward_workforce.py` that returns the module's `Labour`,
so the 365 callers outside labour (screens, mods, the economy port, engine mixins) are unchanged.

- **State**: each seat's people, hours and pay books are `WorkforceSeat` (`sim/workforce/state.py`) and the society's labour hours
  and wage tightness are `WorkforceSociety`; the fields left `HouseholdState`, `ProjectsState`, `FounderState` and `EconomyState` and
  the household facade's field maps (relocations are in `sim/tests/equiv_fields.py`). Readers outside the module read the views
  `staff`, `hour_commitments`, `pay_book`, `training_queue`, `trade_schools`, `worker_housing_places`, `trade_spread`,
  `society_labour_hours`, `staff_version` and `staff_on_all_books`; writers send commands (`AllocateHours`, `ReleaseHours`,
  `OrderWork`, `CancelWork`, `SetReserve`, `DrawTradeHours`, `ResetTradeHours`, `SpendDirectorHours`, `SettleLivingCost`,
  `SetWageHoursSold`, `BleedStaff`, `DisperseDependants`, `LoseCrew`, `WatchStaff`). The payroll dict reports its changes on the
  `staff` channel (`staff_version`), which replaces the household's `_workforce_ver`.
- **Views published** (uncached, because `Labour` writes the seat's people and hours in place and keeps no count of its writes): `staff`, `staff_snapshot`, `headcount`, `hours_available`, `literacy_references`, `literacy_capacity`,
  `farm_share_of_hours`, `trade_spread`, `staff_advice`, `project_staffing_shortfall`, `seat_base_tile`, `market_supply`,
  `trade_available`, `labour_quote`, `hour_wage`, `wage`, `base_annual_wage`, `trade_population`, `money_per_labour_hour`,
  `opening_money_per_labour_hour`, `labour_state_weights`, `town_mortality_premium_by_tile`, `wage_index`, `wage_index_terms`,
  `wage_materials`, `trade_registry` (now with each trade's `training_years`), `society_labour_hours`, `farming_technique`,
  `farm_land_hectares`, `hours_per_person_year` (the working day: lit hours added by open works, moved from `working_day.py`).
- **Commands applied**: `SetEmployed`, `NoteTradeSpread`, `PressLabour`, `SurviveStaff`, `ScaleDeputies`, `ReportStaffReduction`,
  `AllocateFarmWorkforce`, `ApplyLandClearing`, `UpdateWages`, `TakeWageFallback`, `CloseHoursYear`. Two commands of the module are
  still applied by the bridge because the logic they call sits in files other work owns: `NoteWageShock` (`cause_book.py`, shared with
  projects staffing and the screens). `BuildHousing` is the module's now.
- **Phases**: `apprenticeships`, `staff` and `seat_prelude` (teaching the lost trades and the standing work order) are the module's
  hooks; the wage fallback and the end of the year's hours run inside `seat_work` as the two commands above.
- **Rules moved beside it**: the wage index, the lit working day, the reteach, staff-phase, payroll and replacement-mode rules, the
  wave exposure (`sim.workforce.api.wave_exposure`) and the work-order shortfall.

## Not moved, and why

- **Cached views.** None is cached: `Labour` mutates the seat's dicts and counts in place (hundreds of sites in `sim/labour/`), so only
  the payroll dict (`employees`) can report its changes. A view becomes `cached=True` when those writes go through commands that
  bump a channel.
- **`revenue_capacity`** (`sim/engine/economy_production.py`) still sets the hours sold to zero with `SetWageHoursSold` and puts them
  back; it becomes a pure quote when `revenue()` takes the sold hours as an argument.
- **The household facade** keeps `workforce` (the payroll) for the actors' protocol, reading the seat slot (`Household._workforce`).
- **`game_attribute`** (`sim/engine/bridge_seats.py`) answers an attribute-sourced win condition (`slaves`) from the `staff` view
  when `Sim` has no such attribute.
- **`_step_reputation`'s other two owners** (polity's `RenewStanding` and `CloseStandingYear`, the ledger's `spend_last_year`) stay in
  the engine around the module's `CloseHoursYear`.
- **`living_cost`, `training_advice` and `training_queue`** stay bridged: their code is the economy's household bill and projects
  staffing (`projects_training_advice.py`), which move with those owners.
- **The farm facts** (`farm_land`, the year's technique, the ladder and the arable ceiling) are plain attributes of `Sim` that
  agriculture's forwarders and the opening write; the module reads them as views and writes the land and the technique through
  `legacy_game` (the farm workforce is the only writer).
- **`wage_schedule.py`** stays in the engine (`data.py` imports it at load); the module asks for a schedule as the view `wage_schedule_for`.

## Debts left (`legacy_*` and shared bridge views the module reads)

`legacy_state` (labour still reads and writes the seat's household money, bondage and base tile, the holdings' market pressure, the
projects' sets and the built ways in place: `grep -rn "_world.state" sim/labour` lists the sites; the year and the policy are the views
`year` and `founder` now), `legacy_game`, `legacy_acting_household` (the purse, for the module's own steps), `legacy_household_actor`,
`legacy_dice`, `legacy_tree`, `legacy_order`, `legacy_projects`, `legacy_act_as`; the engine's `game_config`, `civilisation`, the trade tables (`trade_records`, `trades_absent`,
`trade_notes`, `trade_family`, `starting_wages`), the actors' staff (`actor_staff_*`), and the projects staffing reads (`staffing_*`,
`venture_*`, `staff_closure_age`, `reopen_units`, `exclusion_reason`, `shared_answer`).

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 11 / 8 |
| Old methods and properties owned (after regrouping) | 58 |
| Of those, referenced from another module's mixin code | 11 (8 classed read-only or pure by Appendix B, 3 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 149 (11 from mixins, 31 only from outside) |
| Views per used name | 0.07 |
| Views that replace exactly one referenced method and no field (one-to-one) | 2 of 11 |
| Views of other modules it reads | 20, from 15 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 2 |

**Existing surface and files.** Existing: `sim/labour/` (50 files, `Labour` is a 13-class mixin composite behind `LabourPortMixin.labour`, `sim/engine/labour_port.py`), `sim/labour/api.py` (48 lines). Outside use: 106 distinct `labour.<member>` names (the plan's measure, section 2 of `MODULE_REGISTRY_PLAN.md`, with `labour` substituted). Engine: `HouseholdBillMixin`, `AllocationNotesMixin`, `HourQueueMixin`, `WorkingDayMixin`, `StaffPhaseMixin`, `LabourPortMixin`, the staff steps in `core_step_phases.py`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `Sim` | `sim/engine/core.py` | 1 | 1 |
| `GoodsMixin` | `sim/engine/economy_goods.py` | 3 | 0 |
| `CreditMixin` | `sim/engine/economy_credit.py` | 3 | 3 |
| `HouseholdBillMixin` | `sim/engine/economy_household_bill.py` | 3 | 0 |
| `ProductionMixin` | `sim/engine/economy_production.py` | 1 | 0 |
| `LabourPortMixin` | `sim/engine/labour_port.py` | 1 | 1 |
| `AllocationNotesMixin` | `sim/engine/allocation_notes.py` | 3 | 1 |
| `HourQueueMixin` | `sim/engine/projects_hour_queue.py` | 3 | 1 |
| `ProgressMixin` | `sim/engine/projects_progress.py` | 10 | 3 |
| `WorkingDayMixin` | `sim/engine/working_day.py` | 2 | 0 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 46 | 2 |
| `StepPhasesMixin` | `sim/engine/core_step_phases.py` | 4 | 0 |
| `StaffPhaseMixin` | `sim/engine/step_phase_staff.py` | 1 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_effective_lab_left`, `_step_standing_work_directive`, `_step_teach_trades`, `_step_wage_fallback`, `active_hours_still_wanted`, `clear_unused_hours_report`, `contract_hours`, `extra_lit_hours_per_day`, `hour_pool_now`, `household_bill_per_person`, `household_dependant_people`, `household_need_floors_per_person`, `lab_max_span`, `last_taught`, `trade_introduced_year`, `unused_hours_is_news`, `wages_earned`, `working_hours_per_person_year`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `WorkforceWorld` and a per-seat dataclass `WorkforceSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.society_labour_hours` | world | agriculture 1 | - |
| `state.economy.wage_tightness_factors` | world | - | - |
| `state.founder.director_hours_spent_founder` | seat | - | core 1, projects 1 |
| `state.founder.living_cost_paid` | seat | - | core 1, finance 1 |
| `state.household.artisans` | seat | <ui> 8, hazards 4, finance 3, ventures 3, <engine-functions> 2, projects 1, +1 more | finance 2, hazards 1 |
| `state.household.commissioned` | seat | - | - |
| `state.household.contract_hours` | seat | - | polity 1 |
| `state.household.directors_extra` | seat | <ui> 3, mechanics 2, finance 2, production 1 | hazards 2, disease 1 |
| `state.household.employees` | seat | <ui> 16, <engine-functions> 8, hazards 6, projects 5, core 2, ventures 2, +5 more | core 2, hazards 2 |
| `state.household.freedmen` | seat | <ui> 3, finance 2, production 1 | finance 1 |
| `state.household.granted_staff` | seat | - | - |
| `state.household.hour_allocations` | seat | <ui> 8, projects 2 | <ui> 4, projects 1 |
| `state.household.hours_this_year` | seat | - | polity 1 |
| `state.household.labour_pressure_records` | seat | - | - |
| `state.household.last_taught` | seat | - | - |
| `state.household.manumitted_total` | seat | <ui> 1 | - |
| `state.household.relocation_hours_this_year` | seat | polity 1 | polity 1 |
| `state.household.reserve_craftsmen` | seat | <ui> 3 | - |
| `state.household.reserve_scholars` | seat | <ui> 3 | - |
| `state.household.scholars` | seat | hazards 4, <ui> 3, <engine-functions> 2, projects 1, finance 1, disease 1, +1 more | finance 1, hazards 1 |
| `state.household.slaves` | seat | <ui> 6, finance 5, production 1 | - |
| `state.household.staff_pay_held` | seat | - | - |
| `state.household.supervision_hours_this_year` | seat | polity 1 | polity 1 |
| `state.household.teaching_hours_this_year` | seat | polity 1, <ui> 1 | polity 1 |
| `state.household.trade_introduced_year` | seat | diffusion 1 | diffusion 1 |
| `state.household.trade_schools` | seat | <ui> 2 | - |
| `state.household.trades_created` | seat | <ui> 3, diffusion 1 | - |
| `state.household.trades_endemic` | seat | diffusion 2, <ui> 1 | diffusion 1 |
| `state.household.training` | seat | <ui> 4, <engine-functions> 1 | - |
| `state.household.unused_hours_reported` | seat | - | - |
| `state.household.wage_hours_this_year` | seat | production 2, polity 1, <ui> 1 | production 2 |
| `state.household.wage_income_this_year` | seat | - | - |
| `state.household.wage_work_last_year` | seat | <ui> 2 | - |
| `state.household.wages_earned` | seat | - | - |
| `state.household.wages_paid` | seat | - | - |
| `state.household.wages_prepaid` | seat | <ui> 4, finance 1 | finance 1 |
| `state.household.work_trade` | seat | <ui> 2 | <ui> 2 |
| `state.household.worker_housing_places` | seat | <ui> 1 | - |
| `state.projects.trade_hours_used` | seat | <ui> 1 | projects 1 |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `staff` | table | yes | The seat's people by trade and class: employees, artisans, scholars, extra directors, slaves, freedmen, reserves, granted staff. Replaces `labour.headcount`, `labour.staff_snapshot`, `labour.settlement_tiles`-style reads; see the labour members table. | `labour`, `labour.headcount`, `labour.staff_snapshot`, `labour.base_tile`, `labour.settlement_tiles`, `labour.staff_capacity`, `labour.idle_specialists`, `labour.sole_supervisors`, `labour.trades_drawn_on`, `labour.available_trades`, `labour.trade_headcount_pending`, `labour.taught_trade_people`, `labour.is_craft_trade`, `labour.unskilled_trade`, `labour.held_technologies`, `labour.hired_cap`, `labour.craft_trades_report`, `labour.workforce_report`, `labour.labour`, `labour.api` | `household.employees`, `household.artisans`, `household.scholars`, `household.slaves`, `household.freedmen`, `household.directors_extra`, `household.reserve_craftsmen`, `household.reserve_scholars`, `household.manumitted_total`, `household.granted_staff`, `household.worker_housing_places`, `household.trade_schools`, `household.training` | - | `workforce` | 33 |
| `hours_available` | keyed | yes | Hours the seat can call on by trade, and the pools it is drawn from (directors, scholars, craft hands, supervision room). Replaces `labour.trade_available`, `hours_you_can_call_on`, `director_pool`, `director_hours_committed`, `craft_hands_available`, `scholar_hands_available`, `supervision_room`, `household_room`. | `hour_priority_queue`, `labour.trade_available`, `labour.hours_you_can_call_on`, `labour.director_pool`, `labour.director_hours_committed`, `labour.craft_hands_available`, `labour.scholar_hands_available`, `labour.supervision_room`, `labour.supervision_room_from`, `labour.household_room`, `labour.hours_reserved`, `labour.hours_for_sale`, `labour.training_hours_per_person`, `labour.farm_share_of_hours`, `labour.resync_pools`, `labour.wage_work_this_year` | - | `staff`, `demography.population` | `workforce`, `hours` | 8 |
| `hour_commitments` | table | yes | Hours committed this year by purpose (allocations, teaching, contracts, relocation, supervision, wage work). | `hour_standing`, `hour_pool_now`, `hours_this_year`, `project_hour_pace`, `active_hours_still_wanted`, `trade_draw_plan`, `trade_shortfall_note`, `trade_shortage_kind`, `trade_demand_vs_supply`, `project_useful_hours`, `lab_max_span`, `_effective_lab_left`, `report_unused_directed_hours` | `household.hour_allocations`, `household.hours_this_year`, `household.wage_hours_this_year`, `household.teaching_hours_this_year`, `household.contract_hours`, `household.relocation_hours_this_year`, `household.supervision_hours_this_year`, `household.unused_hours_reported`, `household.work_trade`, `household.last_taught`, `household.wage_work_last_year`, `household.wage_income_this_year`, `projects.trade_hours_used`, `founder.director_hours_spent_founder` | `staff` | `hours` | 4 |
| `wage` | keyed | no | Wage per hour and per year by trade, the trade that pays best, the standing pay. Replaces `labour.wage_per_hour`, `base_annual_wage`, `standing_job_pay`, `wage_for_hours`, `best_wage_trade`. | `labour.wage_per_hour`, `labour.base_annual_wage`, `labour.standing_job_pay`, `labour.wage_for_hours`, `labour.best_wage_trade`, `labour.wages`, `labour.wage_signature`, `labour.opening_wage_schedule`, `labour.yearly_value_of` | - | `labour_market` | `wages` | 12 |
| `trade_spread` | table | yes | Which trades the seat has created, which are endemic in society, and the year each was introduced. | - | `household.trades_created`, `household.trades_endemic`, `household.trade_introduced_year` | - | `workforce` | 2 |
| `wage_index` | table | no | Wages against the base year; a scarcity-corrected index. | `wage_index` | - | `labour_market` | `wages` | 4 |
| `labour_market` | table | no | The year's market state: supply by trade and area, money per labour hour, who exists and who is reachable. Replaces `labour.market`, `market_supply`, `market_supply_split`, `money_per_labour_hour` (15 uses), `national_trade_population`, `reachable_trade_population`, `people_who_exist`. | `labour.market`, `labour.market_supply`, `labour.market_supply_split`, `labour.money_per_labour_hour`, `labour.national_trade_population`, `labour.reachable_trade_population`, `labour.people_who_exist`, `labour.home_town_population_estimate`, `labour.labour_market`, `labour.local_market_share`, `labour.population_report`, `labour.town_mortality_premium_by_tile`, `labour.need_shares`, `labour.learning_curve`, `labour.STATE_WEIGHTS`, `labour.farming_technique`, `labour._farming_technique`, `economy.labour`, `economy.labour_bids`, `economy.labour_inputs`, `economy.year_labour`, `economy.agent_worker_years_by_recipe` | `economy.society_labour_hours`, `economy.wage_tightness_factors` | `demography.population` | `wages`, `workforce` | 19 |
| `living_cost` | table | yes | What the household's people cost per year: dependants, need floors, bill per person. | `living_cost`, `dependants_cost`, `household_need_floors_per_person`, `household_bill_per_person`, `household_dependant_people`, `HOURS_PER_PERSON_YEAR` | - | `markets.household_prices` | `workforce`, `wages` | 12 |
| `wage_bill` | table | yes | The staff's pay for the year and the part prepaid. Replaces `labour.wage_bill` (16 uses). | `founder_wage_income`, `labour.wage_bill`, `labour.trainee_wage_bill` | `household.wages_prepaid`, `household.wages_earned`, `household.wages_paid`, `household.staff_pay_held` | `staff`, `wage` | `wages` | 3 |
| `staffing_quote` | quote | yes | Whether and at what cost a hire, training, commission, slave purchase, relocation or school would go through. Replaces `labour.hire_check`, `commission_check`, `train_check`, `room_advice`, `staff_advice`, `slave_quote`, `relocation_quote`, `hire_buying_room`, `work_for_wages_dry_run`. | `trade_school_price_per_seat`, `housing_price_per_place`, `labour.hire_check`, `labour.commission_check`, `labour.train_check`, `labour.room_advice`, `labour.staff_advice`, `labour.slave_quote`, `labour.relocation_quote`, `labour.hire_buying_room`, `labour.work_for_wages_dry_run`, `labour.project_staffing_shortfall`, `labour.SLAVE_BASE_PRICE` | - | `staff`, `wage` | - | 5 |
| `literacy_capacity` | table | yes | Scholars effective given literacy, and the literate trades. Replaces `labour.effective_scholars` (14 uses), `literate_capacity`, `literacy_factor`, `LITERATE_TRADES`. | `labour.effective_scholars`, `labour.literate_capacity`, `labour.literacy_factor`, `labour.LITERATE_TRADES`, `labour.LITERACY_REFERENCE_GENERAL`, `labour.LITERACY_REFERENCE_ELITE`, `labour.LITERACY_FACTOR_CAP` | - | `diffusion.literacy`, `staff` | `workforce` | 4 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `trade_spread`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 11 methods are referenced from other modules' mixin code: 10 are replaced by a view here, 1 by a command. 31 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 149 used names, 22 are covered by a view or command through the method itself, 18 through a field alias, 2 are year-phase hooks and 107 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `living_cost`, `project_useful_hours`, `report_unused_directed_hours`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `Hire` | seat, trade, quantity | `labour.hire`, `labour.buy_slaves`, `grant_staff`, `set_employed`, `add_employed`. Methods: `labour.hire`, `labour.buy_slaves`, `labour.grant_staff`, `labour.set_employed`, `labour.add_employed`, `labour.hold_staff_reserve`, `labour.replace_lost_foremen`, `labour.auto_commission_for_blocked`, `labour.keep_flagged_concerns_staffed` | `sim/ui/proto/dispatch_labour.py:412`, `sim/ui/proto/dispatch_money.py:177`, `sim/engine/core_step_phases.py:77`, `sim/engine/step_phase_staff.py:198`, `sim/engine/society_adoption.py:433`, `sim/engine/step_phase_money.py:150`, `sim/engine/projects_completion.py:244`, `sim/labour/labour_market_api.py:133,137`, `mods/bh_orghierarchy_r4k8/hierarchy_commands.py:197` | `no_such_trade`, `cannot_afford`, `no_room`, `not_enough_people` | `household.employees`, `household.artisans`, `household.scholars`, `household.directors_extra`, `household.slaves`, `household.granted_staff` |
| `Fire` | seat, trade, quantity | `labour.fire`, `manumit`, payroll shedding. Methods: `labour.fire`, `labour.manumit`, `labour.log_staff_reduction`, `labour.log_staff_lost` | `sim/ui/proto/dispatch_labour.py:438`, `sim/ui/proto/dispatch_money.py:195`, `sim/engine/staff_replacement.py:58`, `sim/engine/payroll_shed.py:20,23`, `sim/engine/step_phase_money.py:155`, `sim/engine/economy_credit.py:476`, `sim/engine/agents_port_seats.py:14`, `mods/bh_orghierarchy_r4k8/hierarchy_commands.py:184` | `no_such_trade`, `not_enough_staff` | `household.freedmen`, `household.manumitted_total` |
| `CommitHours` | seat, purpose, trade, hours | `labour.work_for_wages`, `train`, `commission`, teaching and project draws: the hours owner checks that hours are not committed twice. Methods: `lab_year_draw`, `labour.work_for_wages`, `labour.train`, `labour.commission`, `labour.roll_staff_year` | `sim/ui/proto/dispatch_labour.py:36,477,520`, `sim/engine/core_step_phases.py:269,305,361`, `sim/engine/step_phase_project_start.py`, `sim/engine/step_phase_projects.py` | `no_hours_left`, `trade_absent` | `household.hour_allocations`, `household.hours_this_year`, `household.wage_hours_this_year`, `household.teaching_hours_this_year`, `household.contract_hours`, `household.relocation_hours_this_year`, `household.supervision_hours_this_year`, `projects.trade_hours_used`, `founder.director_hours_spent_founder`, `household.work_trade`, `household.last_taught`, `household.training` |
| `NoteTradeSpread` | seat, trade, year | Written by adoption when a finished technique spreads a trade. | `sim/engine/society_adoption.py` | none: always applies | `household.trades_created`, `household.trades_endemic`, `household.trade_introduced_year` |
| `NotePay` | seat, kind, amount | Wage and living-cost counters written from the money phase and finance. Methods: `labour.settle_staff_pay`, `labour.close_wage_year`, `labour.update_wages` | `sim/engine/step_phase_money.py:45`, `sim/engine/core.py:499`, `sim/engine/economy_credit.py` | none: always applies | `household.wages_prepaid`, `household.wages_paid`, `household.wages_earned`, `household.wage_income_this_year`, `household.staff_pay_held`, `founder.living_cost_paid` |
| `BuildHousing` | seat, places | `build_worker_housing`. Methods: `build_worker_housing` | `sim/engine/economy_goods.py:579` | `cannot_afford` | - |
| `MoveBase` | seat, tile | `labour.move_base` and `found_trade_school`. Methods: `labour.move_base`, `labour.found_trade_school` | `sim/ui/proto/dispatch_labour.py:563`, `sim/ui/proto/dispatch_money.py:102` | `tile_not_held`, `cannot_afford` | `household.trade_schools`, `household.worker_housing_places` |
| `LoseStaff` | seat, survival_share | Hazard losses of people: `apply_staff_survival`, insolvency bleed, completion. | `sim/engine/society_hazards.py:70-77`, `sim/engine/step_phase_money.py:134-135`, `sim/engine/step_phase_staff.py:219-222`, `sim/engine/projects_completion.py:401-403` | none: always applies | `household.employees`, `household.artisans`, `household.scholars`, `household.directors_extra` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `economy.society_labour_hours`: 1 site: `sim/labour/labour_allocation.py:359`
- `founder.director_hours_spent_founder`: 2 sites: `sim/engine/core.py:493`, `sim/engine/step_phase_projects.py:180`
- `founder.living_cost_paid`: 2 sites: `sim/engine/step_phase_money.py:45`, `sim/engine/core.py:499`
- `household.artisans`: 6 sites: `sim/labour/labour_bondage.py:53`, `sim/labour/labour_bondage.py:129`, `sim/labour/labour_bondage.py:348`, `sim/engine/society_hazards.py:71`, `sim/engine/step_phase_money.py:134`, `sim/engine/economy_credit.py:478`
- `household.commissioned`: 2 sites: `sim/labour/labour_training.py:659`, `sim/labour/labour_settlement.py:198`
- `household.contract_hours`: 3 sites: `sim/labour/labour_training.py:658`, `sim/labour/labour_settlement.py:199`, `sim/engine/core_step_phases.py:412`
- `household.directors_extra`: 3 sites: `sim/engine/shock_year.py:86`, `sim/engine/society_hazards.py:560`, `sim/engine/disease_port.py:303`
- `household.employees`: 6 sites: `sim/agents/household.py:369`, `sim/agents/household.py:237`, `sim/engine/society_hazards.py:75`, `sim/engine/society_hazards.py:77` (.pop()), `sim/engine/core.py:604`, `sim/engine/economy.py:253`
- `household.freedmen`: 2 sites: `sim/labour/labour_bondage.py:333`, `sim/engine/economy_credit.py:477`
- `household.granted_staff`: 1 site: `sim/labour/labour_bondage.py:49`
- `household.hour_allocations`: 5 sites: `sim/ui/proto/dispatch_labour.py:144` (assign (alias)), `sim/ui/proto/dispatch_labour.py:121` (assign (alias)), `sim/ui/proto/dispatch_labour.py:139` (.pop() (alias)), `sim/ui/proto/dispatch_labour.py:102` (.pop() (alias)), `sim/engine/projects_completion.py:202` (.pop())
- `household.hours_this_year`: 1 site: `sim/engine/core_step_phases.py:391` (assign (alias))
- `household.manumitted_total`: 1 site: `sim/labour/labour_bondage.py:334`
- `household.relocation_hours_this_year`: 2 sites: `sim/labour/labour_settlement.py:195`, `sim/engine/core_step_phases.py:414`
- `household.scholars`: 4 sites: `sim/labour/labour_bondage.py:52`, `sim/labour/labour_bondage.py:132`, `sim/engine/society_hazards.py:70`, `sim/engine/step_phase_money.py:135`
- `household.slaves`: 2 sites: `sim/labour/labour_bondage.py:276`, `sim/labour/labour_bondage.py:332`
- `household.staff_pay_held`: 1 site: `sim/labour/labour_staff_pay.py:29`
- `household.supervision_hours_this_year`: 1 site: `sim/engine/core_step_phases.py:415`
- `household.teaching_hours_this_year`: 2 sites: `sim/labour/labour_training.py:487`, `sim/engine/core_step_phases.py:413`
- `household.trade_introduced_year`: 1 site: `sim/engine/society_adoption.py:403`
- `household.trade_schools`: 1 site: `sim/labour/labour_population.py:98`
- `household.trades_created`: 2 sites: `sim/labour/labour_training.py:488` (.add()), `sim/labour/labour_population.py:100` (.add())
- `household.trades_endemic`: 1 site: `sim/engine/society_adoption.py:407` (.add())
- `household.training`: 4 sites: `sim/labour/labour_training.py:340`, `sim/labour/labour_training.py:491` (.extend()), `sim/labour/labour_bondage.py:279` (.append()), `sim/engine/core_step_phases.py:94`
- `household.wage_hours_this_year`: 6 sites: `sim/labour/labour_wage_ledger.py:29`, `sim/labour/labour_wage_ledger.py:49`, `sim/labour/labour_wages.py:119`, `sim/engine/core_properties.py:65`, `sim/engine/economy_production.py:123`, `sim/engine/economy_production.py:127`
- `household.wage_income_this_year`: 3 sites: `sim/labour/labour_wage_ledger.py:30`, `sim/labour/labour_wage_ledger.py:49`, `sim/labour/labour_wages.py:121`
- `household.wage_work_last_year`: 1 site: `sim/labour/labour_wage_ledger.py:28`
- `household.wages_earned`: 2 sites: `sim/labour/labour_wage_ledger.py:49`, `sim/labour/labour_wages.py:120`
- `household.wages_prepaid`: 2 sites: `sim/labour/labour_training.py:302`, `sim/engine/step_phase_money.py:44`
- `household.work_trade`: 2 sites: `sim/ui/proto/dispatch_labour.py:122` (assign (alias)), `sim/ui/proto/dispatch_labour.py:103` (assign (alias))
- `household.worker_housing_places`: 1 site: `sim/engine/economy_goods.py:580`
- `projects.trade_hours_used`: 2 sites: `sim/engine/step_phase_projects.py:449`, `sim/engine/projects_progress.py:262`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `demography`: `demography.population` (input of workforce.hours_available, input of workforce.labour_market)
- `diffusion`: `diffusion.literacy` (input of workforce.literacy_capacity)
- `disease`: `disease.coverage` (coverage_nodes, coverage_share)
- `finance`: `finance.credit_limit` (credit_limit)
- `knowledge`: `knowledge.techniques_held` (projects.done)
- `ledger`: `ledger.acting_balance` (household.capital)
- `markets`: `markets.agent_economy` (economy, economy.agent_need_floor_costs_at); `markets.household_prices` (input of workforce.living_cost)
- `materials`: `materials.resource_throttle` (peek_project_resource_throttle)
- `mechanics`: `mechanics.effect` (effect_values); `mechanics.mechanic` (mechanic, nodes_with_mechanic)
- `production`: `production.revenue_estimate` (held_trade, revenue); `production.running` (running); `production.upkeep` (upkeep)
- `projects`: `projects.active_projects` (projects.active, projects.bountied); `projects.start_check` (start_reason)
- `reporting`: `reporting.event_log` (household.log)
- `resources`: `resources.mine_cost` (mine_operating_cost)
- `seats`: `seats.founder` (founder.policy)
- `ventures`: `ventures.staffing_shortfalls` (staffing_closed_hand_shortfall)

Sends (commands of other modules):

- `ledger`: `PayEdge`
- `reporting`: `RecordEvent`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `apprenticeships`
- `staff`
- `money_seat`: the living-cost and wage postings and auto-buy of people (`step_phase_money.py:53,149-155`)
- `seat_work`: `_step_teach_trades`, `_step_standing_work_directive`, `_step_wage_fallback`, and the hours capture and tally reset inside `_step_reputation`

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 276 | `labour`, `employees`, `artisans`, `hour_allocations`, `wage_index`, `slaves`, `living_cost`, `scholars` |
| engine/(function modules) | 39 | `labour`, `scholars`, `artisans`, `employees`, `living_cost`, `wage_index`, `_step_apprenticeships`, `_step_staff` |
| labour | 22 | `labour`, `HOURS_PER_PERSON_YEAR`, `wage_index` |
| engine/agents_port* | 19 | `labour`, `HOURS_PER_PERSON_YEAR`, `patron_funding_ask`, `patron_clients` |
| mods | 17 | `labour`, `employees`, `HOURS_PER_PERSON_YEAR` |
| economy | 13 | `labour` |
| engine/economy_port* | 10 | `labour`, `HOURS_PER_PERSON_YEAR` |
| constants.py | 3 | `labour` |
| agents | 3 | `labour` |
| engine/mod* | 1 | `labour` |
| engine/ui* | 1 | `labour` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: 174 uses of `labour.<member>` and about 100 reads of staff fields; `sim/economy` 13 uses of `labour`; `sim/labour` itself reads 22 engine names through `LabourWorld`; mods: 13 uses of `labour`.

## (h) Hard spots and caches

- `Labour` takes the whole `Sim` through the `LabourWorld` adapter (`sim/engine/labour_port.py`, 150 inbound references in the mixins). Becoming a module means `LabourWorld` turns into a declared view list; every `self._world.<name>` in sim/labour is a read to list (count with `grep -rn '_world\.' sim/labour | wc -l`; not measured here).
- The year clearing (`run_labour_year`) is an iterative market clear over trades and areas; it is internal to workforce and reads prices and population as views, never as methods.
- `household.employees` is an `_InvalidatingDict` that calls `_workforce_changed` (sim/invalidating.py, `economy.py:253`); that wrapper becomes a `workforce` channel bump on every command.
- Three people records (STATE_OWNERSHIP_MAP.md): `sim.population`, `record.workforce` and `household.employees`; a view must say which it means.
- `_step_reputation` (`core_step_phases.py:368-420`) is a year-close step with three owners: it decays reputation and familiarity (polity), captures `hours_this_year` and then resets the hour tallies and `contract_hours` (this module), and captures `spend_last_year` (ledger). Split it into three phase hooks; the capture must run before the reset.
- Staffing is read by projects start inside the same year after hires; `hours_available` must be fresh after each `CommitHours` (versioned per seat).

Caches and version counters held today (feed for task 1.2):

- `_workforce_changed`/`_reset_workforce` and `household.workforce_version` (`sim/agents/household.py:467`, `economy.py:253`)
- `__dict__['_labour']` (`labour_port.py:387`): the package instance, rebuilt on load

Detected by the cache scan in this module's mixin files: `engine/labour_port.py:387 __dict__[_labour]`.
