# Module `seats`

Seats and the acting context: who plays, joining and handing over, goals and win conditions, the founder's life, dealings between seats, and what one seat sees of another.

**Status:** moved (branch `mr/seats`). The package is `sim/seats/`; this file describes what shipped, not the draft proposal. The seat registry (`state.seats`), `act_as`, `_switch_seat`, the household facades and `sync_seat_facades` stay on `Sim` (plan 4.7): the module reads the registry's ids through the `registered_seats` view and changes it only by the commands `RegisterSeat` and `MoveSeat`, which `sim/engine/bridge_seats.py` applies for good. Counts come from the spec (`python3 -c "import sys; sys.path.insert(0,'.'); from sim.seats.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies), len(s[0].reads), len(s[0].sends))"`).

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

Real module views: `tree`, `tree_nodes`, `techniques_held`, `techniques_granted` (knowledge); `disclosures`, `copy_difficulty`, `literacy` (diffusion); `running_mechanics`, `corpus_dispersed` (mechanics); `year`, `civilisation`, `price_index` (existing bridge entries of the root). Answered by the bridge, named for the owner that will publish them: `seat_party` (keyed) and `seat_party_with_margins` (actors: the facade lives on `Sim`), `seat_base_tile` (workforce), `seat_holds` (what a handover would overwrite in the engine's own state), `seeded_actor_registry` (actors; reading it seeds the opening cast, a read that writes), `society_techs`, `kit_capital`, `founder_life_terms`, `generation_breakdown` (materials: the breakdown, where the existing `generation` view is only the total), `hazard_relief` and `hazard_relief_entries` (hazards), `patronage` (`{founder_age, deputies, deputy_hours, deputies_carry_the_work}`, mechanics), `dissolution_terms` (the `declare`d constants of a dissolving programme, which stay on `Sim`), `losable_node_ids` (knowledge/mechanics). `legacy_*`: `game_random`, `legacy_actor_registry`, `legacy_agent_world`.

**Bridged for good (until the owner moves):** `win_condition_text` (it is `data.win_condition_describe`, which the UI uses too) and `on_road_to_goal` (its cache `_goal_closure` lives on `Sim` and is also read by `labour_port.py`, `society_hazards.py` and the UI). `ForgetGoalCaches` is applied by the engine for the same reason.

## Commands sent

`RegisterSeat`, `MoveSeat`, `ForgetGoalCaches` (applied by the bridge), `LearnTechnique`, `ForgetTechnique`, `RevealNodes` (knowledge), `RekeyDisclosures` (diffusion), `RecordEvent` (reporting).

## Forwarders left (`sim/engine/forward_seats.py`)

`playing_seats`, `ended_seats`, `run_over`, `acting_country`, `governed_countries`, `society_techs_now`, `join_seat`, `join_cast_seats`, `hand_over_seat`, `seat_place`, `dealing_party`, `dealings_listing`, `seat_patent`, `seat_offer`, `seat_answer`, `set_goal`, `record_goal_reached`, `win_condition_anatomy`, `_win_condition_value`, `forget_goal_caches`. Callers: the UI (`ui_port`, `dispatch_seats`, `dispatch_dealings`, `goals_watch`, `anatomy`), `year_phases.py`, `agents_port*.py`, `economy_port*.py`, `disease_port.py`, `shock_year.py`, `society_hazards.py`, `world_hazards.py`, `projects_completion.py`, `seat_bank.py`. The properties `goal`, `policy` stay on `ForwardingPropertiesMixin`; `goal_year`, `founder_alive`, `life_left` there are read-only views of the module (`dead_reason`'s setter sends `EndRun`).

## Year phases

`hear_of_other_seats`, `win_conditions` and the new `founder_mortality` are the module's. `drop_ended_seats` (a world phase that asks `ended_seats`), `begin_seat_year` and `advance_year` stay in `year_phases.py`.

## Debts

- Every outside writer of a founder's death or a seat's goal now sends a command: `core.py` (`SetFounderLife` at the opening), `society_hazards.py` (`_catastrophe` sends `EndRun`), `cli.py` and `cli_interactive.py` (`SetFounderLife`), the `dead_reason` setter (`EndRun`, no log line). Readers of the moved fields in `sim/labour` reach the founder's life through `LabourWorld.founder_alive`.
- The seat's goal, country, kind, holder and policy are `SeatsSeat` fields; `legacy_seats` is gone and the registry's ids are the bridge view `registered_seats`. A handover moves the leaver's slot to the replacement, which keeps its own founder life and policy.
- The dissolution count (`stalled`) is the seat state; forgetting a node stops its plant by `StopOperating` (ventures).
- A country seat has no founder, but its slot carries `founder_alive`, `life_left`, `dead_reason` at their defaults; on the base they were absent. The equivalence tool's micro tier has no country seat; a run with one would show those three leaves as new.
- `HouseholdParty` (agents) is handed the slot (`dealings=`), because the agents package cannot name the seats module.

## Hard spots

- A read that writes: `governed_countries` seeds the opening cast the first time it is asked (`seeded_actor_registry`), and `seat_base_tile` switches the acting seat for the read (`act_as`). Both are bridge views for that reason.
- `join_seat` draws the founder's lifespan from the game's random source even for a country seat (which has no founder), and before the registry is checked for a duplicate id. Both are kept: the draw order is part of the game.
- The handover refusal reads `holds` from two places: the engine's own state (`seat_holds`: works, staff, arrears, holdings, institutions, the remaining progress record) and the module's (disclosures count as works, dealings as holdings, a goal year as a goal record); the refusal lists them in the old order (`HOLD_ORDER`).

## Width review

Measure: `python3 tools/measure/module_graph.py --modules` (declaration counts). This review dropped three reads and left the number of modules depended on unchanged: each of the three came from an owner the module still needs for something else. `READS_BY_OWNER` in `sim/seats/module_spec.py` now groups every read under the module that publishes it (the old labels listed `core` for what scenario publishes and `workforce (people)` as a second group for a workforce view).

### 1. What it depends on, by what it asks

| Asked of | What | Where in the module |
|---|---|---|
| scenario, prices | the year, the civilisation's record and cast, the fog-of-war and automation settings, the game random source, the founder's life terms and kit capital, the price index | `founder.py`, `run.py`, `join_rules.py`, `sight.py`, `dealings.py` |
| knowledge | the tree and its closure, techniques held, granted, revealed and by seat, the nodes a founder could lose; sends `LearnTechnique`, `ForgetTechnique`, `RevealNodes` | `goals.py`, `sight.py`, `founder.py`, `run.py`, `module.py` |
| diffusion | each seat's disclosures, copy difficulty, the literacy figure; sends `RekeyDisclosures` | `sight.py`, `builds.py`, `handover.py`, `royalty.py`, `goals.py` |
| mechanics | the mechanics running, whether the corpus is dispersed | `founder.py` |
| workforce | staff (directors, the staff-number goals), a seat's base tile; sends `WatchStaff` | `founder.py`, `goals.py`, `sight.py`, `run.py` |
| ventures, projects, ledger | what each seat operates; sends `WatchBusiness`, `StopOperating`, `WatchActive`, `OpenPurse` on a join | `sight.py`, `builds.py`, `run.py` |
| materials, hazards, content | the generation breakdown, the relief of an epidemic, the labels of a win condition | `goals.py` |
| actors | the seeded registry (which countries have a government) and the state's treasury id | `run.py` |
| assembly | the registry's ids and what a handover would overwrite; sends `AddSeat`, `MoveSeat` | `run.py`, `handover.py`, `sight.py`, `module.py` |
| reporting | sends `RecordEvent` | `goals.py`, `founder.py` |

### 2. Findings

**(a) Views that mirror one method.** Knowledge's four views of the seats' techniques (`techniques_held`, `techniques_granted`, `techniques_revealed`, `techniques_by_seat`) are four cuts of one table, asked together in `sight.py` and `founder.py`; ventures' `operating_by_seat` answers what `operating` answered for one seat (the `operating` read was declared and never asked; removed). Hazards' `hazard_relief` and `hazard_relief_entries` are the value and its parts for one metric, asked in one function. These are the owners' views (knowledge, hazards); the merge is for their reviews. Seats' own published views were checked for the same: `seat_country`, `seat_kind` and `seat_holder` are keyed reads of the registry entry's fields with different callers; `win_condition_value` and `win_condition_anatomy` differ by what the caller asks (the number, or its parts); none is a mirror of a method with one reader.

**(b) Sub-domains that read a separate set of owners.**

| Sub-domain | Files | Reads that nothing else in the module needs |
|---|---|---|
| Goals and win conditions | `goals.py`, `goal_rules.py`; views `goal`, `on_road_to_goal`, `goal_closure`, `goal_critical_floor`, `win_condition_text`, `win_condition_value`, `win_condition_anatomy`; commands `SetGoal`, `RecordGoalReached`, `RememberGoalClosure`, `ForgetGoalClosure`, `RememberGoalFloor`; the `win_conditions` phase and the `win_condition_rows` point | content (labels), hazards (relief), materials (generation breakdown), diffusion (`literacy`), the tree's closure |
| The founder's life | `founder.py`, `founder_rules.py`; views `founder`, `patronage`, `dissolution_terms`, `automatic_policy`; commands `SetFounderLife`, `SetPolicy`, `EndRun`; the `founder_mortality` phase | mechanics (running, dispersed), the automation and game config, `game_random`, `losable_node_ids` |
| Seeing and dealing | `sight.py`, `sight_rules.py`, `visibility.py`, `dealings.py`, `dealing_rules.py`, `royalty.py`, `builds.py` | diffusion (disclosures, copy difficulty), ventures (`operating_by_seat`), the place of a seat |
| Joining and handing over | `run.py`, `handover.py`, `join_rules.py`, `handover_rules.py`, `lists.py` | actors, ledger, projects, ventures (the watches and the purse), the assembly, kit capital |

**(c) Pass-throughs.** Removed: the `actor_world` read, used only to ask the actors' world for one great-circle distance between two seats' places (`distance_between_seats`); the distance is a geography call now (`sim/geography/places.py`, `distance_between_places`), and the actors' world calls the same one. `cast` was declared and never asked. Left: the `state_treasury` read hands the id of the state's account to `SetSeatHolder` and nothing else; and `governed_countries` reads the whole seeded registry (a read that writes: it seeds the opening cast) for two facts, the countries and whether each has a government. The actors already publish `has_state` and `countries`, which answer other questions (`has_state` is whether an owner has soldiers to raise, not whether a government exists); an actors view `governed_countries` would answer the question the seats ask and let the seats drop `seeded_actor_registry` and `state_treasury`'s id (the join could ask `holder_treasury`). Not done: it changes who publishes the view, and the readers outside the module (`grep -rn governed_countries sim`) need to follow; it needs a test on a game with a partner country.

### 3. Done, and proposed

Done, each commit with the quick tier green and values unchanged:

- `distance_between_seats` computes the distance with `sim/geography/places.py`; the read of the actors' world is gone. Test: `sim/tests/test_geography_places.py` (the two places' great circle, and no distance for an id the map does not have).
- The `cast` and `operating` reads dropped (declared, never asked).
- The spec's reads regrouped by their real owner.

Proposed, not built:

- **Goals as their own module (`goals`).** Move `goals.py`, `goal_rules.py` and the goal part of `constants.py`, the views and commands in the table above, and the `win_conditions` phase and `win_condition_rows` point. The seats would drop content, hazards, materials and `literacy` (and `tree_closure`, `generation_breakdown`); the new module takes them, plus a read of the seats' `acting_seat` and `seat_list`. The seat registry stays with the seats; the goal id is an alias of the seat entry (`SeatState.goal`), so the module would write it with a command. Edge count of the seats falls by content, hazards and materials; goals starts with about as many as the three it took.
- **The founder's life** could go with it (one `founder` module), taking mechanics out of the seats; it is the part that reads the game's random source and config. Left together here because `EndRun` is sent by the win-condition check and the handover reads `founder`.
- **The actors' `governed_countries`** (2(c) above).
- Knowledge's one view for what a seat holds, granted and revealed, and hazards' one view of an epidemic's relief (2(a)): the seats would read two views fewer each.

### 4. Why the remaining edges are needed

A seat is a player's whole state (techniques, staff, businesses, projects, purse, disclosures), so joining and handing over send to each owner of one of those (watches, purse, rekeying, learning), and what other seats can see of it is read from the same owners. The goals measure what the seat has done, in the owners' terms. Scenario's reads are the game's own settings. These are the unavoidable edges of a module whose subject is the player; the ones in the proposals above are the part a different module could hold.
