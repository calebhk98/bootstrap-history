# Module `hazards`

Dated shocks and world hazards, and what counters them: the dated catastrophes of a civilisation's file, the yearly chances that need
no date, the base-rate shocks every country draws for, famine watch, the relief that built defences give, the advice and timeline the
screens print, the world event log and the world's output factor.

**Status:** moved, on branch `mr/hazards` (package `sim/hazards/`, bridge `sim/engine/bridge_hazards.py`, forwarders
`sim/engine/forward_hazards.py`). The draft of task 1.5 (a read-only analysis of `e8b004c`) is replaced by what the move found; "What
the move changed in this draft" lists each correction. Re-measure counts with `python3 -c "import sys; sys.path.insert(0,'.'); from
sim.hazards import module_spec as m; s=m.MODULE_SPECS[0]; print(len(s.publishes), len(s.applies), len(s.reads), len(s.sends))"`.

## What the move changed in this draft

- **Views: fourteen quotes and tables, not four.** The draft grouped the figures into `hazard_figures`, `hazard_relief`, `knowledge_risk`
  and `output_factor`. Callers ask for one figure with arguments (the kind of harm, the hazard, the nodes to assume running), so
  each is a quote (`hazard_figure`, `hazard_relief_entries`, `hazard_relief`, `hazard_relief_detail`, `hazard_effect_preview`,
  `hazard_advice`, `hazard_timeline`, `staff_loss_exposure`, `national_public_health_sources`), which never needs a cache and
  clears the three-caller floor by being a quote. Tables: `output_factor`, `disaster_this_year`, `countries_in_game`;
  quotes of the log and the calendar: `world_events`, `live_hazard_kinds` (was published by the living-stock bridge, now here).
- **`knowledge_risk` and `_epidemic_risk` stay in `fog.py`** (the knowledge module owns that file). Nothing in this module calls
  them: the screens and `knowledge_warning` call `sim.knowledge_risk`, which reads this module's figures through the forwarders. They
  go to whichever module takes `fog.py`; `losable_node_ids` was their other input; `corpus_hedge` is the knowledge module's (it moved there first).
- **Commands applied: three, not two.** `RecordWorldEvent` (the log's one writer; was applied by the campaigns bridge),
  `LoseCapital` (a catastrophe destroys a share of what the acting household holds; the epidemic step and the state's demands still
  call `lose_capital`) and `RecoverOutput` (the year's recovery of the output factor, sent by the money phase). `SetOutputFactor` is
  not a command: the factor falls only inside this module's shocks and rises only by `RecoverOutput`. `RunRandomEvents` is the
  phase `random_events`, not a command.
- **Commands sent: seventeen, of which eleven are new classes** in the owners' packages and applied by `bridge_hazards.py`: workforce
  `SurviveStaff`, `ScaleDeputies`, `ReportStaffReduction`, `NoteWageShock`; demography `CutPopulation`, `RefreshDemographicIndexes`,
  `KillPeople`; polity `ScaleProtection`; projects `ResetProjectProgress`, `ShutForgotten`; seats `FounderDies`; the knowledge module's `ForgetTechnique` carries the lost nodes.
  The draft's `ChangeStanding` is not one command (the invented command meant different things in two prototypes): scandal is
  `RaiseScandal` (existing), protection is `ScaleProtection`. `LearnTechnique`, `StartProject`, `SetOperating`, `Hire`, `Fire`,
  `CloseWork`, `ChargeTheft` and `PayEdge` as listed in the draft are not sent: the old code never hired, fired or started anything,
  and `ChargeTheft` is `PlunderHousehold`.
- **A sack sends `ShutForgotten` (the works stop running or sit shut) and then one `ForgetTechnique` with all the nodes.** The old
  loop told the caches once; the knowledge module bumps once per command, so one command keeps the saved counter identical.
- **State: four world fields and one seat field, not two world fields.** `HazardsWorld`: `output_factor`, `world_events`,
  `said_output`, `said_debasement` (the last two were `ScenarioState._said_output` and `_said_debasement`); `HazardsSeat`:
  `last_patron_death` (was `FounderState.last_patron_death`). `said_condition` (was `ScenarioState._said_condition`) is hazards' too, a per-seat set: the concern levy marks its notices through the command `SayOnce`. Relocations are in `sim/tests/equiv_fields.py`.
- **`_catastrophe` is not hazards'.** Nothing in this module calls it; the three callers are in `core_step_phases.py` (denounced, too
  eminent, no successors). It is the seats' command `FounderDies`; `Sim._catastrophe` forwards.
- **Constants moved with the module** (`sim/hazards/constants.py`): the seventeen declared numbers of the three mixins, the
  output recovery rate from `core.py` (the corpus hedge pair went to knowledge), and the two own-mine counter shares from `projects_completion.py`
  (20 `declare` calls, `grep -c "= declare(" sim/hazards/constants.py`).
  `PATRON_DEATH_COURTING_GIFT` (a descriptor pricing the hours in the coin) is gone: the module multiplies the hours by
  `money_per_labour_hour` and the price index itself, in the old order.
- **Pure helpers moved in** (`git mv`): `hazard_condition`, `hazard_window`, `hazard_hedge_timing`, `hazard_merge`, `hazard_toll`,
  `hedge_steps`, `patron_death`, `capital_loss`, `staff_loss_words`, `world_hazard_data` (now `window.py`, `condition.py`, ...).
  `war_relief` moved from `military_rules.py` to `rules.py`; `leverage_of` stays there (polity's).
- **The 25 reads from 14 modules are 50 views from 20 owners**, because the old code reached further than the catalogue's scan: the
  seat switch (`acting_as`), the dice (`game_random`), the event-cause evaluator (`effective_hazard`), the tree's critical path
  and closure, the founder's policy, the goal, the wage index, the mines, the strata. Which are bridged is in "Reads" below.
- **The draft's "needs a second consumer" for `hazard_relief`** no longer applies: it is a quote.

## Mixin classes and files absorbed

| Old class | Old file | Now |
|---|---|---|
| `ShockYearMixin` | `sim/engine/shock_year.py` | `sim/hazards/shocks.py` (`Shocks`) |
| `HazardsMixin` | `sim/engine/society_hazards.py` | `sim/hazards/random_events.py`, `sack.py`, `advice.py`, `shocks.py` (the condition and cause steps), `constants.py` |
| `HazardReliefMixin` | `sim/engine/hazard_relief.py` | `sim/hazards/relief.py` (`Relief`) |
| `WorldHazardsMixin` and the functions around it | `sim/engine/world_hazards.py`, `world_events.py` | `sim/hazards/world.py`, `events.py` |
| `Sim.corpus_hedge`, `OUTPUT_RECOVERY_RATE`, the output factor property | `sim/engine/core.py`, `core_properties.py` | `relief.py`, `events.py`, forwarders |
| `StepPhasesMixin._step_dated_shocks` | `sim/engine/core_step_phases.py` | `Shocks.step_dated_shocks` |

The plain rules are in `sim/hazards/rules.py` (counter strength, the product of reliefs, the output floor, exposure, the corpus a sack
faces, the output factor's fall and recovery, the timeline's urgency, the log's records, the famine reading), the data readers in
`world_data.py`.

## State owned

`HazardsWorld`: `output_factor` (1.0 to leave output whole), `world_events` (dated records, `{year, kind, actors, tiles, cause,
facts}`, the last `event_log_years_kept` years), `said_output`, `said_debasement`. `HazardsSeat`: `last_patron_death`.

## Views published

| View | Kind | Seat | Answers | Channels |
|---|---|---|---|---|
| `output_factor` | table | no | the economy's share of normal real output | `output_factor` (cached: written only here) |
| `world_events` | quote | no | the log's records, by kind, from a year on, or involving an actor | - |
| `hazard_figure` | quote | yes | the harm a hazard does of one kind after what is built | - |
| `hazard_relief_entries` | quote | yes | one record per defence in force against a kind | - |
| `hazard_relief`, `hazard_relief_detail` | quote | yes | the multiplier (and what did it, and what lapsed) | - |
| `hazard_effect_preview` | quote | yes | what building a node would do to each hazard ahead | - |
| `hazard_advice`, `hazard_timeline` | quote | yes | what kind of thing helps, with first steps and lead time; one line per hazard ahead | - |
| `staff_loss_exposure` | quote | yes | the staff a household loses to one wave | - |
| `national_public_health_sources` | quote | yes | the medical work that has spread through the country | - |
| `live_hazard_kinds` | quote | no | the kinds of hazard in progress in a year | - |
| `disaster_this_year` | table | no | this year's dated hazards and what the acting seat's log said of them | no |
| `countries_in_game` | table | no | the home country and the partners whose people live in the agent economy | no |

## Commands applied

| Command | Fields | Answers |
|---|---|---|
| `RecordWorldEvent` | kind, actors, tiles, cause, facts | the record written |
| `LoseCapital` | fraction, cause | the money destroyed (0.0 for a debt or an empty purse) |
| `RecoverOutput` | - | nothing |

## Phases

`dated_shocks`, `random_events`, `world_hazards`, `famine_watch` are `PhaseHook`s; their `SHIPPED` entries are
`module_world_phase(...)`. The output factor's recovery inside `money_world` stays in that phase as a `RecoverOutput` it sends.
`check_yearly_world` (the multi-country invariants) is engine auditing that reads `countries_in_game`; it stays a forwarder.

## Commands sent to other owners

`PayEdge` (ledger), `PlunderHousehold` (coin), `ErodeMoney`, `RecordEvent` (reporting), `RaiseScandal`, `ScaleProtection`,
`ShiftValueWeight` (polity), `LoseStaff` (workforce), `NoteWageShock` (reporting), `CutPopulation`,
`RefreshDemographicIndexes`, `KillPeople` (demography), `ForgetTechnique` (knowledge), `ResetProjectProgress`, `ShutForgotten` (projects).

## Reads

Views of finished modules: `year`, `civilisation`, `seat_list`, `techniques_held`, `techniques_granted`, `tree`, `tree_nodes`, `running`,
`start_check`, `project_cost`, `visible_to_player`, `hazard_counter_rows`, `corpus_hedge_tiers`, `corpus_nodes`, `mechanic`,
`running_mechanics`, `civ_diffusion`, `diffusible_ids`, `diffusion_relief`, `counter_supply_gap`, `standing`, `automation`,
`money_per_labour_hour`, `price_index`, `money_text`, `money_real`, `event_log`, `acting_balance`, `staff`, `partners_in_agent_economy`,
`weather_seed`, `game_random`.

Published by `bridge_hazards.py` under the name the owner will publish (each is deleted when its owner moves): `events_enabled`,
`ended_seats`, `founder`, `goal` (seats); `losable_node_ids`, `critical_path`, `tree_closure` (knowledge and the tree); `active_projects`,
`closure_record`, `closed_by_choice` (projects and ventures); `military_leverage` (polity); `wage_index`
(workforce); `country_strata` (actors). The event-cause evaluator (`effective_hazard`, `event_cause_report`) is the module's own
(`causes.py`, `cause_quantities.py`, `cause_rules.py`, `cause_report.py`); each quantity reads a view of its owner: actors
`state_budget_figures`, `army_figures`, `state_knows`, `home_strata_rows`; land `tiles_listed_by`; demography
`population_total`, `nutrition_ratio_last_year`; reporting `real_output_hours`; diffusion `literacy`; scenario `opening_civilisation`.

Debts, raw objects or switches the module cannot do without: `acting_as` (the module has no way to switch seats; the world
phases act as each seat in turn), and the reused `game_random`.

## Forwarders left (`sim/engine/forward_hazards.py`)

`hazard_figure`, `hazard_relief_entries`, `hazard_relief`, `hazard_effect_preview`, `hazard_advice`, `hazard_timeline`,
`staff_loss_exposure`, `national_public_health_sources`, `output_floor`, the properties `output_factor` and
`disaster_this_year`, `check_yearly_world`, `lose_capital`, `apply_staff_survival`, `_surviving_people`, `_catastrophe`, and ten
constants other code and mods still read off the game. Callers: the screens (`sim/ui`), `fog.py`, `goals.py`,
`disease_port.py`, `state_demand.py`, `projects_completion.py`, `projects_rebuild.py`, `core.py`, `core_step_phases.py` and the
`bh_cashshelter_z6f2` mod.

## Hard spots, as resolved

- **Dice order.** The module draws in the old order, once per call: the yearly chance of a wave, the attack averted and the sack
  chance, the corpus roll and its sample, then the patron, fire and banditry. `SurviveStaff` rolls one die per person in the bridge
  with the game's dice, in the old order (scholars, artisans, then each trade sorted). The micro equivalence check hashes the
  generator every year.
- **A hazard writes into eight owners' fields**: each is now a command above. The sack's four writes (plunder, staff, deputies,
  projects) keep the old order, and the staff-loss wave keeps the deputies before the log (the log's staffing check reads them).
- **Quirks kept on purpose**: the staff-loss message is built outside `act_as`, so its national-sources sentence reads the acting
  (first) seat's techniques; the goal's closure is computed once for the module and reused for every seat. Both were in the
  old code.
- **Reads that write.** `hazard_effect_preview` and the figures only read. The remaining writers are the phases and the three
  commands.
- **The `risk` screen** (`fog.knowledge_risk`) still calls the quotes through the forwarders; moving it is the knowledge module's.

## Width review

Measure: `python3 tools/measure/module_graph.py --modules` (reads, sends and modules depended on); the reads by publisher are
`python3 -c "from sim.hazards.module_spec import READS_BY_OWNER as table; [print(owner, names) for owner, names in table.items()]"`
(regrouped under the module that publishes each view). Grouping the package's files by the views they read shows four parts that
share little: the shocks, sack and random events (`shocks.py`, `sack.py`, `random_events.py`, `capital_loss.py`, `patron_death.py`),
the figures that say what counters a hazard (`relief.py`, `advice.py`, `cause_*.py`, `causes.py`, `window.py`, `condition.py`), the
knowledge-loss rules (`knowledge_risk.py`, the corpus half of `sack.py`, `hedge_*.py`) and the world hazards (`world.py`,
`world_data.py`, `events.py`).

### What it depends on, by what it asks

| Asks of | What for | Reads and sends |
|---|---|---|
| scenario, seats, ledger, reporting | The year, the civilisation's dated hazards, the game's dice, who plays, the purse and the log | `year`, `civilisation`, `opening_civilisation`, `events_enabled`, `game_random`, `automation`, `fog_of_war`, `money_text`; `seat_list`, `ended_seats`, `founder`, `goal`; `acting_balance`, sends `PayEdge`; `event_log`, `money_real`, `real_output_hours`, sends `RecordEvent`, `ErodeMoney`, `NoteWageShock` |
| knowledge, mechanics | What the seat holds and may lose, and the counters data names | `techniques_held`, `techniques_granted`, `techniques_forgotten`, `tree`, `tree_nodes`, `visible_to_player`, `visibility`, `losable_node_ids`, `tree_closure`, `critical_path`, `corpus_hedge`, send `ForgetTechnique`; `hazard_counter_rows`, `corpus_nodes`, `mechanic`, `running_mechanics` |
| production, projects, ventures, defence_stores, resources, diffusion, land | What defences stand: what runs, what is built or closed, what is stocked, what the nation has adopted | production `running`, `capability_gaps`; projects `start_check`, `project_cost`, `active_projects`, `closure_record`, `closed_by_choice`, send `ResetProjectProgress`; ventures send `ShutForgotten`; defence_stores `counter_supply_gap`; resources `mine_capacity`; diffusion `civ_diffusion`, `diffusible_ids`, `diffusion_relief`, `literacy`; land `tiles_listed_by` |
| workforce, demography, polity, coin | What a shock does to people, population, standing and cash | workforce `wage_index`, `money_per_labour_hour`, send `LoseStaff`; demography `population_total`, `nutrition_ratio_last_year`, sends `CutPopulation`, `RefreshDemographicIndexes`, `KillPeople`; polity `military_leverage`, `standing`, sends `RaiseScandal`, `ScaleProtection`, `ShiftValueWeight`; coin send `PlunderHousehold` |
| actors, agriculture, foreign_trade, disease, prices | The countries and the dice and figures the world hazards and the cause figures need | actors `country_strata`, `state_budget_figures`, `army_figures`, `state_knows`, `home_strata_rows`; agriculture `weather_seed`; foreign_trade `partners_in_agent_economy`; disease `epidemic_risk`; prices `price_index` |

### Findings

**(a) Mirror views.**

- Done, `LoseStaff` (workforce): the plague wave and the sack each read `staff` and `staff_snapshot`, sent `SurviveStaff`,
  `ScaleDeputies` and `ReportStaffReduction`, and counted the people either side from `staff`. One command now takes the snapshot,
  rolls the survival, scales the deputies, logs the fall and answers the people on the books before and after. The module reads
  neither view and sends one command for three; disease, which did the same, changed with it.
- Done, dead read: `corpus_hedge_tiers` was declared and never read.
- Kept, knowledge's `visible_to_player(node)` and `visibility(node, memo)`: `visible_to_player` adds a tree-membership test, and
  `knowledge_risk.py` asks about a hedge id that may not be a tree node, so the two answer differently there.
- Open, not built, knowledge's `tree(node)` and `tree_nodes()`: `tree[node]` is `tree_nodes().get(node)`. The module reads both; every
  reader of `tree` in other modules (including seats and materials, which other reviews own) would switch to `tree_nodes`.
- Open, not built: `money_per_labour_hour` (workforce) times `price_index` (prices) is read for one figure, the patron's courting gift
  (`random_events.py`); a `labour_hours_value(hours)` view would give it as one question; agriculture (`farm.py`) multiplies the same two.

**(b) Sub-domains that read their own set of owners** (measured by grouping the files above by the views each reads):

- The world hazards (`world.py`, `world_data.py`, with `data/world/world_hazards.json`; the phases `world_hazards` and `famine_watch`)
  read scenario, seats, actors `country_strata`, agriculture `weather_seed` and foreign_trade `partners_in_agent_economy`, and send
  `KillPeople`, `RecordEvent` and this module's `RecordWorldEvent`. Agriculture and foreign_trade are read nowhere else in the module.
  Proposal: a `world_hazards` module holding those files; it sends `RecordWorldEvent` to hazards for the log, as other modules do, and
  hazards stops depending on agriculture and foreign_trade. Moving the world event log (`events.py`, the `WORLD_EVENTS` channel) with it
  is the alternative, but the log is also written by the shocks, so it stays.
- The hazard figures (`relief.py`, `advice.py`, `cause_quantities.py`, `cause_report.py`, `cause_rules.py`, `causes.py`, `window.py`,
  `condition.py`) are the only part that reads defence_stores, diffusion, land and resources, and the bulk of the knowledge, projects,
  actors and polity reads. The shocks call them back as the module's own views (`hazard_relief_detail`, `effective_hazard`). Proposal:
  a `defences` module publishing the figure views (`hazard_figure`, `hazard_relief`, `hazard_relief_entries`, `hazard_relief_detail`,
  `hazard_effect_preview`, `hazard_advice`, `hazard_timeline`, `effective_hazard`, `event_cause_report`, `national_public_health_sources`,
  `staff_loss_exposure`); hazards would read those and drop defence_stores, diffusion, land and resources. The callers of those views
  (the seats module, the screens) change their owner name only.
- The knowledge-loss rules (`knowledge_risk.py`, the corpus half of `sack.py` and `hedge_*.py`) are the only part that reads disease
  `epidemic_risk` and sends `ShutForgotten` and `ForgetTechnique`, and they read knowledge's own views. They are knowledge's questions
  (what can be lost, what hedges it) asked in this module. Proposal: move them to the knowledge module (they were `fog.py`'s before the
  hazards move); hazards would send it the sack's roll and drop disease and ventures.

**(c) Pass-through dependencies.**

- Fixed: `staff_snapshot` was read only to hand it to workforce's `ReportStaffReduction`.
- `quantity.read(self.needs, ...)` (`causes.py`) hands the module's own needs to the table of reader functions in `cause_quantities.py`,
  one per fact a dated event's cause may name; they are the module's reads, not a hand-off to another module.
- Nothing else is read only to be forwarded.

### What was done, and why each remaining edge is needed

Done (each a commit, quick tier green, values identical): `LoseStaff` and the dead read; the reads grouped by publisher. Every other
edge is something a shock or a defence is made of: a hazard hits people, cash, population, standing, projects and the written corpus
(each owned by another module, so each a command), and what counters it is read from what runs, what is built, what is stocked and what
the nation has adopted (each a view). The three proposals above separate the parts whose owners are disjoint; the first two would
take the module from the widest set of owners to a set each part reads in full.
