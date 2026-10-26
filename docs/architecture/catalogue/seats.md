# Module `seats`

Seats and the acting context: who plays, goals and win conditions, the founder's life, dealings between seats.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 6 / 6 |
| Old methods and properties owned (after regrouping) | 42 |
| Of those, referenced from another module's mixin code | 11 (5 classed read-only or pure by Appendix B, 6 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 33 (11 from mixins, 20 only from outside) |
| Views per used name | 0.18 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 6 |
| Views of other modules it reads | 15, from 11 modules |
| Commands of other modules it sends | 6 |

**Existing surface and files.** Existing: `sim/assembly/clock.py`, `sim/engine/state_seat.py` (`SeatState`, `bind_seat`). Engine: `SeatMixin` (`act_as`), `SeatRunMixin`, `SeatHandoverMixin`, `SeatBuildsMixin`, `SeatSightMixin`, `SeatDealingsMixin`, `GoalsMixin`, win-condition methods of `Sim`, `_step_founder_mortality`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `Sim` | `sim/engine/core.py` | 2 | 1 |
| `SeatMixin` | `sim/engine/core_seats.py` | 2 | 1 |
| `SeatRunMixin` | `sim/engine/seat_run.py` | 11 | 4 |
| `SeatHandoverMixin` | `sim/engine/seat_handover.py` | 1 | 0 |
| `SeatBuildsMixin` | `sim/engine/seat_builds.py` | 2 | 0 |
| `SeatSightMixin` | `sim/engine/seat_sight.py` | 2 | 1 |
| `SeatDealingsMixin` | `sim/engine/seat_dealings.py` | 7 | 1 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 16 | 4 |
| `GoalsMixin` | `sim/engine/goals.py` | 4 | 1 |
| `StepPhasesMixin` | `sim/engine/core_step_phases.py` | 2 | 0 |
| `MoneyPhaseMixin` | `sim/engine/step_phase_money.py` | 1 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_check_win_conditions`, `_new_founder_years`, `_new_seat_policy`, `_refuse_unsupported`, `_step_founder_mortality`, `_what_survived_the_dissolution`, `distance_between_seats`, `each_playing_seat`, `find_dealer`, `forget_goal_caches`, `seats_that_built`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `SeatsSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.founder._founder_death_aged` | seat | - | <engine-functions> 1 |
| `state.founder._founder_death_year` | seat | - | <engine-functions> 1 |
| `state.founder.dead_reason` | seat | <ui> 3 | core 1, hazards 1, <ui> 1 |
| `state.founder.founder_alive` | seat | <ui> 9, ventures 4, projects 1, polity 1, production 1 | core 1, <ui> 1 |
| `state.founder.last_patron_death` | seat | hazards 1 | hazards 1 |
| `state.founder.life_left` | seat | - | <ui> 2, core 1 |
| `state.founder.policy` | seat | <ui> 10, projects 7, workforce 4, finance 4, polity 1, hazards 1 | core 1, <ui> 1 |
| `state.holdings.offer_serial` | seat | - | - |
| `state.holdings.offers` | seat | - | - |
| `state.holdings.patents` | seat | - | - |
| `state.holdings.shares_held` | seat | - | - |
| `state.holdings.shares_issued` | seat | - | - |
| `state.household.base_tile` | seat | - | - |
| `state.household.saving_for` | seat | <ui> 1 | <ui> 2 |
| `state.household.saving_target` | seat | <ui> 1 | <ui> 2 |
| `state.seat_progress.dashboard_history_years` | seat | <ui> 2 | <ui> 1 |
| `state.seat_progress.goal_year` | seat | <ui> 25, <engine-functions> 4 | - |
| `state.seat_progress.goal_years` | seat | <engine-functions> 1 | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `acting_seat` | table | yes | The acting seat id, kind, country, holder. | `acting_country`, `goods_market.acting`, `goods_market.acting_party_id` | - | - | `seat` | 5 |
| `seat_list` | table | no | Seats playing, ended, joined; whether the run is over; governed countries; society techs now. | `playing_seats`, `ended_seats`, `run_over`, `governed_countries`, `society_techs_now`, `seats_that_built`, `seat_place` | - | - | `seats` | 9 |
| `goal` | table | yes | The seat's goal, the year reached, the record of goals reached, the win condition anatomy and value. Replaces the forwarding properties `goal`, `goal_year` (UI: 52 and 30 reads). | `win_condition_anatomy`, `_win_condition_value`, `goal`, `goal_year` | `seat_progress.goal_year`, `seat_progress.goal_years`, `seat_progress.dashboard_history_years`, `household.saving_for`, `household.saving_target` | `knowledge.techniques_held` | `goal` | 10 |
| `founder` | table | yes | The founder's life: alive, years left, cause of death, policy, last patron death. Replaces forwarding properties `policy`, `founder_alive`, `life_left`, `dead_reason`. | `policy` | `founder.founder_alive`, `founder.life_left`, `founder.dead_reason`, `founder.policy`, `founder.last_patron_death` | - | `founder` | 10 |
| `seat_party` | keyed | no | A seat as a party to dealings and to the goods market. | `seat_party`, `seat_parties`, `dealing_party` | - | - | `seats` | 6 |
| `dealings` | table | yes | Offers made and received, patents held, shares held and issued; the listing. | `dealings_listing`, `find_dealer`, `distance_between_seats` | `holdings.patents`, `holdings.shares_held`, `holdings.shares_issued`, `holdings.offers`, `holdings.offer_serial` | - | `dealings` | 1 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `dealings`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 11 methods are referenced from other modules' mixin code: 8 are replaced by a view here, 3 by a command. 20 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 33 used names, 25 are covered by a view or command through the method itself, 5 through a field alias, 1 are year-phase hooks and 2 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_win_condition_value`, `dealing_party`, `dealings_listing`, `distance_between_seats`, `find_dealer`, `seat_parties`, `seat_party`, `seat_place`, `win_condition_anatomy`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `AddSeat` | template | `add_seat`, `join_seat`, `join_cast_seats`. Methods: `join_cast_seats`, `join_seat` | `sim/engine/core_seats.py`, `sim/engine/seat_run.py` | `seat_exists` | - |
| `SetGoal` | seat, goal | `set_goal`, `record_goal_reached`. Methods: `record_goal_reached`, `set_goal` | `sim/ui/proto/dispatch_goals.py`, `sim/engine/goals.py` | `unknown_goal` | `seat_progress.goal_year`, `seat_progress.goal_years`, `seat_progress.dashboard_history_years`, `household.saving_for`, `household.saving_target` |
| `FounderDies` | seat, cause | `_step_founder_mortality`, hazards that kill the founder. | `sim/engine/core_step_phases.py (_step_founder_mortality)`, `sim/engine/society_hazards.py` | none: always applies | `founder.founder_alive`, `founder.life_left`, `founder.dead_reason`, `founder.last_patron_death`, `founder._founder_death_aged`, `founder._founder_death_year`, `founder.policy` |
| `MakeOffer` | seat, to, kind, terms | `seat_offer`, `seat_answer`, `seat_patent`. Methods: `seat_offer`, `seat_answer`, `seat_patent` | `sim/engine/seat_dealings.py` | `no_such_seat`, `unsupported` | `holdings.patents`, `holdings.shares_held`, `holdings.shares_issued`, `holdings.offers`, `holdings.offer_serial` |
| `HearOfOtherSeats` | seat, other | `hear_of_other_seats`: a seat that hears of another reveals nodes to it (`observer.revealed.update`); sends RevealNodes. Methods: `hear_of_other_seats` | `sim/engine/seat_sight.py` | none: always applies | - |
| `HandOverSeat` | seat, to | `hand_over_seat`. Methods: `hand_over_seat` | `sim/engine/seat_handover.py` | `not_playing` | - |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `founder._founder_death_aged`: 1 site: `sim/engine/ui_port.py:161` (assign (alias))
- `founder._founder_death_year`: 1 site: `sim/engine/ui_port.py:161` (assign (alias))
- `founder.dead_reason`: 3 sites: `sim/ui/proto/dispatch_inspection.py:94` (assign (alias)), `sim/engine/society_hazards.py:790`, `sim/engine/core.py:492`
- `founder.founder_alive`: 2 sites: `sim/ui/cli_interactive.py:809` (assign (alias)), `sim/engine/core.py:491`
- `founder.last_patron_death`: 1 site: `sim/engine/society_hazards.py:742`
- `founder.life_left`: 3 sites: `sim/ui/cli.py:1201` (assign (alias)), `sim/ui/cli_interactive.py:807` (assign (alias)), `sim/engine/core.py:495`
- `founder.policy`: 2 sites: `sim/ui/proto/dispatch_ventures.py:766` (assign (alias)), `sim/engine/core.py:482` (assign (alias))
- `holdings.offers`: 1 site: `sim/engine/seat_handover_rekey.py:26`
- `holdings.shares_held`: 1 site: `sim/engine/seat_handover_rekey.py:27` (.pop())
- `household.base_tile`: 1 site: `sim/labour/labour_settlement.py:203`
- `household.saving_for`: 2 sites: `sim/ui/proto/dispatch_saving.py:18`, `sim/ui/proto/dispatch_saving.py:29`
- `household.saving_target`: 2 sites: `sim/ui/proto/dispatch_saving.py:19`, `sim/ui/proto/dispatch_saving.py:30`
- `seat_progress.dashboard_history_years`: 1 site: `sim/ui/proto/dispatch_game_options.py:43`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.get, actors.government_of, actors.state)
- `diffusion`: `diffusion.disclosure` (copy_difficulty); `diffusion.literacy` (literacy)
- `hazards`: `hazards.hazard_relief` (hazard_relief, hazard_relief_entries)
- `knowledge`: `knowledge.techniques_held` (input of seats.goal, projects.done, projects.done_year, projects.granted); `knowledge.visibility` (projects.revealed)
- `materials`: `materials.generation` (generation_breakdown_kw)
- `mechanics`: `mechanics.corpus` (corpus_is_dispersed, losable_node_ids); `mechanics.patronage` (deputies_carry_the_work, founder_age)
- `polity`: `polity.state_treasury` (state_treasury)
- `production`: `production.running` (projects.operating, running_with_mechanic); `production.techniques_in_use` (_society_held_techs)
- `projects`: `projects.active_projects` (projects.stalled)
- `reporting`: `reporting.event_log` (household.log)
- `workforce`: `workforce.staff` (labour, labour.base_tile)

Sends (commands of other modules):

- `hazards`: `RunRandomEvents`
- `knowledge`: `LearnTechnique`, `RevealNodes`
- `production`: `SetOperating`
- `projects`: `ResetProgress`
- `reporting`: `RecordEvent`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `begin_seat_year`: `hear_of_other_seats` (`core_step_phases.py:110-116`)
- `win_conditions`
- `drop_ended_seats`
- `seat_work`: `_step_founder_mortality`
- `advance_year`

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 125 | `goal`, `goal_year`, `policy`, `founder_alive`, `dead_reason`, `dealings_listing`, `seat_offer`, `life_left` |
| engine/(function modules) | 9 | `goal_year`, `ended_seats`, `_step_win_conditions`, `playing_seats` |
| engine/agents_port* | 8 | `playing_seats`, `seat_party`, `seat_place`, `seat_parties` |
| engine/ui* | 4 | `_founder_death_aged`, `_founder_death_year`, `set_goal`, `win_condition_anatomy` |
| engine/economy_port* | 3 | `playing_seats` |
| engine/saveload* | 2 | `goal` |
| agents | 1 | `seat_parties` |
| engine/save* | 1 | `goal` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `goal` 52, `goal_year` 30, `policy` 11, `founder_alive` 10, `dealings_listing` 3, `seat_offer` 3; agents_port: `act_as` 5, `playing_seats` 3, `seat_party` 3; economy_port: `act_as` 4, `playing_seats` 3; engine functions: `act_as` 8.

## (h) Hard spots and caches

- `act_as` is the only switch (CLAUDE.md, plan 4.2 Seats): it rebinds `state.household/projects/holdings/founder/...` aliases (`bind_seat`, `state_seat.py:61`) and the `_seat_facades` (`core_seats.py`). In the new design it becomes one `bump_seat(seat)` and seat-scoped views read the acting seat; the base module keeps `Sim`'s `act_as` context manager.
- A country seat has no household or founder (`SeatState.kind == COUNTRY_SEAT`), only an empty placeholder household the aliases need; seat-scoped views must answer for a seat that owns no household.
- `_seat_facades` and `_wrap_seat_containers` rewrap `_InvalidatingDict`s per seat (`core.py:593-606`).

Caches and version counters held today (feed for task 1.2):

- `_seat_facades` (`core.py:468`), `_founder_death_cache` (`ui_port.py:169`)
