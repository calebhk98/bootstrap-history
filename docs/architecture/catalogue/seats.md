# Module `seats`

Seats and the acting context: who plays, joining and handing over, goals and win conditions, the founder's life, dealings between seats, and what one seat sees of another.

**Status:** moved (branch `mr/seats`). The package is `sim/seats/`; this file describes what shipped, not the draft proposal. The seat registry (`state.seats`), `act_as`, `_switch_seat`, the household facades and `sync_seat_facades` stay on `Sim` (plan 4.7): the module reads the registry through the `legacy_seats` view and changes it only by the commands `RegisterSeat` and `MoveSeat`, which `sim/engine/bridge_seats.py` applies for good. Counts come from the spec (`python3 -c "import sys; sys.path.insert(0,'.'); from sim.seats.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies), len(s[0].reads), len(s[0].sends))"`).

## What changed from the draft

- **Views: 18 instead of 6, and different ones.** The draft's `seat_list` kept its bridged shape (`{joined, playing}`, the first publisher's) and the other seat questions each got their own view, because their callers ask them separately: `ended_seats`, `run_over`, `dead_reasons` (the text of why each ended seat ended, for the seats screen), `acting_country`, `played_countries`, `governed_countries`, `seat_holders`, `built_by_any_seat`, `seat_place` (keyed), `distance_between_seats`. `acting_seat` stays the id (a string), not the draft's table of id, kind, country and holder: the kind, country and holder are fields of the registry's entries and the seats screen reads them from `state.seats`. Dealings are `dealings_listing` and `dealing_party` (the seat as a party to an exchange; the seat bank mutates it, so it is a live handle, not a copy). `goal` and `founder` are seat-scoped tables as proposed (`{node, year, years}` and `{alive, life_left, dead_reason}`). `win_condition_value` and `win_condition_anatomy` are quotes. `dealings` was under the three-caller floor and became the listing.
- **Commands: 10 applied, 3 sent and applied by the bridge, not 6.** `JoinSeat`, `JoinCastSeats`, `HandOverSeat`, `SetGoal`, `RecordGoalReached`, `ApplyForPatent`, `MakeOffer`, `AnswerOffer`, `EndRun` (the run ends for the acting seat; `announce` False is the "asked for the score" end that logs nothing), `SetFounderLife`. The draft's `FounderDies` is `EndRun` plus the `founder_mortality` phase: a death by age is the phase's, an end by denunciation, a fall or a dissolution is `EndRun`'s. `HearOfOtherSeats` is the `hear_of_other_seats` phase, not a command. `RegisterSeat` and `MoveSeat` (the registry's own changes) and `ForgetGoalCaches` (the goal caches live on `Sim`) are sent by the module and applied by the engine. A refusal is a `Refusal` with a cause (`unknown_starting_techs`, `no_government`, `seat_exists`, the handover's four); the old `join_seat` raised `ValueError` and still does at the forwarder, with the same message.
- **A new phase, `founder_mortality`.** `_step_founder_mortality` ran at the end of `_run_seat_work`; it is now its own seat phase placed right after `seat_work`, so the order is the old one. `seat_work` keeps its name for the part before it (a mod's `after: seat_work` still runs after the progress, reputation and bondage steps; one that wants to run after the death step names `founder_mortality`).
- **State moved into the seat slot (`SeatsSeat`)**, each with a relocation in `sim/tests/equiv_fields.py`: `goal_year`, `goal_years` (from `SeatProgressState`); `patents`, `shares_held`, `shares_issued`, `offers`, `offer_serial` (from `HoldingsState`); `founder_alive`, `life_left`, `dead_reason` (from `FounderState`).
- **Not moved, against the draft.** `seat_progress.dashboard_history_years` is a dashboard option the UI sets (reporting's, not a goal). `household.saving_for` and `saving_target` are the household's savings plan (`dispatch_saving.py`). `founder.last_patron_death` is the memory of the patron-death event (hazards'). `founder._founder_death_aged` and `_year` are the UI's memory of a death it announced. `founder.policy` has readers in every owner (projects, workforce, finance, polity, hazards, ui: `grep -rn "founder.policy" sim | wc -l`); it stays on `FounderState` until those owners move. `household.base_tile` is workforce's (the seat's place is read through `seat_place`). `SeatState.goal` (the chosen goal id), `country`, `kind`, `holder` are the registry's entries and stay with the seat.
- **Moved to plain-value rules** in `sim/seats/`: `lists.py` (`seats_playing`, `seats_ended`, `run_is_over`), `builds.py` (`builders_of`, `holders_of`, `built_by_any`, `operating_anywhere`, `disclosure_modes`, `licensors_of`), `royalty.py`, `country.py`, `visibility.py` (how much of an invention an onlooker sees: the actors' world and a seat's sight both use it, and `years_to_be_believed` is the disclosure rule), `sight_rules.py`, `join_rules.py`, `handover_rules.py`, `goal_rules.py` (`win_condition_met` included), `dealing_rules.py`, `founder_rules.py` (the mortality arithmetic and the words of the death, the dissolution and the ending).
- **The win-condition anatomy hook became an extension point.** `GoalsMixin.WIN_CONDITION_ANATOMY` was a class dict of `metric -> function(sim, condition)`; nothing in the repository used it but one test. It is now `win_condition_rows(condition) -> rows or None` (first answer wins), which a mod provides with `api.provide("seats.win_condition_rows", fn)`.
- **Dead code deleted.** `each_playing_seat` and `seats_that_built` (no callers), `WIN_CONDITION_METRICS` (no readers), `Sim._step_money` and `_step_win_conditions` (nothing called `_step_money`; the `win_conditions` phase is the module's).

## Mixin classes and files absorbed

| Old | Now |
|---|---|
| `SeatRunMixin` (`seat_run.py`) | `run.py` (`Run`), `lists.py`; forwarders in `sim/engine/forward_seats.py` |
| `SeatHandoverMixin`, `seat_handover.py` | `handover.py` (`Handover`), `handover_rules.py`; the registry move is `sim/engine/seat_move.py` (applied for `MoveSeat`); `seat_handover_empty.py` and `seat_handover_rekey.py` stay in the engine (they read engine state dataclasses and the engine's own stores) |
| `SeatBuildsMixin`, `seat_builds.py` | `builds.py` (the one method, `seats_that_built`, had no caller; `seat_place` is `Sight.seat_place`) |
| `SeatSightMixin`, `seat_sight.py` | `sight.py`, `sight_rules.py` |
| `SeatDealingsMixin`, `seat_dealings.py` | `dealings.py`, `dealing_rules.py` |
| `GoalsMixin`, `goals.py`; `_win_condition_value`, `_check_win_conditions`, `_win_condition_keys` in `core.py` | `goals.py`, `goal_rules.py` |
| `seat_royalty.py`, `seat_country.py`, `engine/visibility.py`, `win_condition_rule.py` | `royalty.py`, `country.py`, `visibility.py`, `goal_rules.py` |
| `_step_founder_mortality`, `_deputy_*`, `_what_survived_the_dissolution` (`core_step_phases.py`) | `founder.py`, `founder_rules.py` |
| `ForwardingPropertiesMixin.goal_year`, `founder_alive`, `life_left`, `dead_reason` | read the `goal` and `founder` views; `dead_reason` is written by `EndRun`; `goal` (the id) stays an alias of the seat |

`SeatBankMixin` (`seat_bank.py`) is not in the catalogue's list and stays in the engine; it reads `dealing_party` through a forwarder. `seat_defaults.py` (the default policy) stays: policy stays on `FounderState`.

## State owned

`SeatsSeat` (`sim/seats/state.py`): `goal_year`, `goal_years`, `patents`, `shares_held`, `shares_issued`, `offers`, `offer_serial`, `founder_alive`, `life_left`, `dead_reason`. No world state. A handover moves the whole slot with the seat except the founder's life: the replacement keeps its own founder, so the module saves the replacement's three fields before `MoveSeat` and writes them back after.

## Views published

| View | Kind | Seat | Answers |
|---|---|---|---|
| `acting_seat` | table | no | the id of the seat acting now (`clock.acting_seat`) |
| `acting_country` | table | yes | the partner country the acting seat belongs to, or None |
| `seat_list` | table | no | `{joined, playing}` ids in joining order |
| `ended_seats`, `dead_reasons`, `run_over` | table | no | the ended seats, why each ended, whether no seat has anything more to play |
| `played_countries`, `governed_countries` | table | no | the countries a country seat plays; those with a government a country seat can hold |
| `seat_holders`, `built_by_any_seat` | quote | no | which seats hold a node; which of some nodes a seat built |
| `seat_place`, `distance_between_seats` | keyed / quote | no | a seat's base tile; great-circle km between two seats |
| `goal`, `founder` | table | yes | the goal, its year and the years reached; whether the founder lives, years left, why the run ended |
| `win_condition_value`, `win_condition_anatomy` | quote | yes | the number behind a measurement goal, and its parts |
| `dealing_party`, `dealings_listing` | table | yes | the seat as a party to an exchange; its patents, shares and waiting offers |

None is cached: the registry, the held sets and the founder's death are written outside the module's commands (see "Debts"). `win_condition_text` and `on_road_to_goal` are still published by the bridge under seats' names (see "Bridged").

## Reads, and what the bridge still answers (`sim/engine/bridge_seats.py`)

Real module views: `tree`, `tree_nodes`, `techniques_held`, `techniques_granted` (knowledge); `disclosures`, `copy_difficulty`, `literacy` (diffusion); `running_mechanics`, `corpus_dispersed` (mechanics); `year`, `civilisation`, `price_index` (existing bridge entries of the root). Answered by the bridge, named for the owner that will publish them: `seat_party` (keyed) and `seat_party_with_margins` (actors: the facade lives on `Sim`), `seat_base_tile` (workforce), `seat_holds` (what a handover would overwrite in the engine's own state), `seeded_actor_registry` (actors; reading it seeds the opening cast, a read that writes), `society_techs`, `kit_capital`, `founder_life_terms`, `game_attribute` (an attribute-sourced win condition reads `getattr(sim, path)`), `generation_breakdown` (materials: the breakdown, where the existing `generation` view is only the total), `hazard_relief` and `hazard_relief_entries` (hazards), `patronage` (`{founder_age, deputies, deputy_hours, deputies_carry_the_work}`, mechanics), `dissolution_terms` (the `declare`d constants of a dissolving programme, which stay on `Sim`), `losable_node_ids` (knowledge/mechanics). `legacy_*`: `legacy_seats`, `legacy_projects`, `legacy_fog`, `legacy_dice`, `legacy_actor_registry`, `legacy_agent_world`.

**Bridged for good (until the owner moves):** `win_condition_text` (it is `data.win_condition_describe`, which the UI uses too) and `on_road_to_goal` (its cache `_goal_closure` lives on `Sim` and is also read by `labour_port.py`, `society_hazards.py` and the UI). `ForgetGoalCaches` is applied by the engine for the same reason.

## Commands sent

`RegisterSeat`, `MoveSeat`, `ForgetGoalCaches` (applied by the bridge), `LearnTechnique`, `ForgetTechnique`, `RevealNodes` (knowledge), `RekeyDisclosures` (diffusion), `RecordEvent` (reporting).

## Forwarders left (`sim/engine/forward_seats.py`)

`playing_seats`, `ended_seats`, `run_over`, `acting_country`, `governed_countries`, `society_techs_now`, `join_seat`, `join_cast_seats`, `hand_over_seat`, `seat_place`, `dealing_party`, `dealings_listing`, `seat_patent`, `seat_offer`, `seat_answer`, `set_goal`, `record_goal_reached`, `win_condition_anatomy`, `_win_condition_value`, `forget_goal_caches`. Callers: the UI (`ui_port`, `dispatch_seats`, `dispatch_dealings`, `goals_watch`, `anatomy`), `year_phases.py`, `agents_port*.py`, `economy_port*.py`, `disease_port.py`, `shock_year.py`, `society_hazards.py`, `world_hazards.py`, `projects_completion.py`, `seat_bank.py`. The properties `goal`, `policy` stay on `ForwardingPropertiesMixin`; `goal_year`, `founder_alive`, `life_left` there are read-only views of the module (`dead_reason`'s setter sends `EndRun`).

## Year phases

`hear_of_other_seats`, `win_conditions` and the new `founder_mortality` are the module's. `drop_ended_seats` (a world phase that asks `ended_seats`), `begin_seat_year` and `advance_year` stay in `year_phases.py`.

## Debts

- Every outside writer of a founder's death or a seat's goal now sends a command: `core.py` (`SetFounderLife` at the opening), `society_hazards.py` (`_catastrophe` sends `EndRun`), `cli.py` and `cli_interactive.py` (`SetFounderLife`), the `dead_reason` setter (`EndRun`, no log line). Readers of the moved fields in `sim/labour` reach the founder's life through `LabourWorld.founder_alive`.
- `legacy_seats` is the registry itself; it goes only when `state.seats` does. The module mutates seat entries through it in three places: `SetGoal` writes `SeatState.goal`, `RecordGoalReached` reads it, and the join and handover read `kind`, `country` and the projects' held sets.
- `legacy_projects().stalled` and `.operating` are written by the dissolution step (projects' fields, not yet commands).
- A country seat has no founder, but its slot carries `founder_alive`, `life_left`, `dead_reason` at their defaults; on the base they were absent. The equivalence tool's micro tier has no country seat; a run with one would show those three leaves as new.
- `HouseholdParty` (agents) is handed the slot (`dealings=`), because the agents package cannot name the seats module.

## Hard spots

- A read that writes: `governed_countries` seeds the opening cast the first time it is asked (`seeded_actor_registry`), and `seat_base_tile` switches the acting seat for the read (`act_as`). Both are bridge views for that reason.
- `join_seat` draws the founder's lifespan from the game's random source even for a country seat (which has no founder), and before the registry is checked for a duplicate id. Both are kept: the draw order is part of the game.
- The handover refusal reads `holds` from two places: the engine's own state (`seat_holds`: works, staff, arrears, holdings, institutions, the remaining progress record) and the module's (disclosures count as works, dealings as holdings, a goal year as a goal record); the refusal lists them in the old order (`HOLD_ORDER`).
