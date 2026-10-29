# Module `polity`

A seat's standing with its society and its state, and the state's pressure on it: reputation, scandal, eminence, familiarity,
protection, how the household answers the state's demands, the state's notice, requisition, office and confiscation, how far its
officials reach, the interest groups, the one-off transfers and levies the household pays the state, and what a patron state funds.
It also applies the commands that change the records of a country's state (its army's losses, its tiles' unrest, its risings and
its ruler) and the society's value weights.

**Status:** moved, on branch `mr/polity` (package `sim/polity/`, bridge `sim/engine/bridge_polity.py`, forwarders
`sim/engine/forward_polity.py`). The draft of task 1.5 (a read-only analysis of `e8b004c`) is replaced by what the move found; "What
the move changed in this draft" lists each correction. Re-measure counts with `python3 -c "import sys; sys.path.insert(0,'.'); from
sim.polity import module_spec as m; s=m.MODULE_SPECS[0]; print(len(s.publishes), len(s.applies), len(s.reads), len(s.sends))"`.

## What the move changed in this draft

- **Views: not the draft's seven.** Callers ask one question each, so the draft's `standing` kept the name and shape the projects
  prototype published (`protection`, `scandal`, `bribes_year_to_date`) and gained the rest of the seat's figures; `eminence` stays its own
  view (the coin module reads it alone). The state's questions are published under the names callers already used: `state_reach`,
  `order_reach`, `inspection_reach`, `forest_reach`, `state_authority`, `visible_scale` (a quote), `military_leverage`,
  `state_interest`, `value_weight`, `start_gate_group_prohibition`. The draft's `state_treasury` table, which mixed the government actor
  with the state's asks, is not one view: the government actor is the cast's (the actors module), published by the bridge as
  `state_treasury`; the asks are `levy_shares`, `notice_over`, `household_scale`, `state_notice`, `state_pressure_report`.
  `state_account` and `interest_groups` stayed under the three-caller floor and are tables of the screens (`state_debt`,
  `interest_groups`, `interest_groups_report`): the screens are the callers.
- **Commands applied: twenty-five.** The fourteen the stability, hazards, projects, diffusion and living-stock modules already sent
  (`RaiseScandal`, `RecordBribe`, `ScaleProtection`, `GainReputation`, `ShiftValueWeight`, `StrikeFromForce` and the eight records of
  a country's state, applied by four bridge files until now), and eleven new ones for what other code wrote straight into the seat's
  fields: `AddScandal` (a finished work's alarm; a group's blame), `AddReputation` (a manumission's standing), `SetReputation` (the
  trial figure the settlement sets and puts back; a finance debt), `ScaleFamiliarity` (a move leaves part of the city behind),
  `AddGovernance` (a work the state values), `AnswerStateDemands`, `WithdrawFromPublicLife`, `SettleWithState` (the screens),
  `CarryOutTransfers` (a finished work that declares a transfer), and the two halves of the year (`RenewStanding`,
  `CloseStandingYear`). The draft's `ChangeStanding` and `RunStatePressure` are not commands: nothing sends them. `PayState` is
  `Polity.pay_state`, used only inside the module.
- **`_step_reputation` is split in the order it ran.** The first part (reputation toward its floor, familiarity) is
  `RenewStanding`; the hours tallied for workforce, `spend_last_year` for the ledger and the market pressure stay in the engine's
  step, in between; the rest (eminence's warning, protection, the state's pressure and the concern levies, scandal, bribery, the two
  hazards that end a run) is `CloseStandingYear`. `begin_seat_year` (the scandal mark) was wholly polity's and is the `PhaseHook`
  `begin_seat_year`.
- **State: one seat dataclass `PolitySeat`, no world state.** The fields: `reputation`, `scandal`, `scandal_last_year`, `eminence`,
  `familiarity`, `protection`, `gov` (the whole of `GovernanceState`), `demand_stance`, `service_offer`, `concealed`, `defiance`,
  `bribes_ytd`, `atrocity` (written and read by nobody), `last_withdrawal`, `last_military_demand`, and the warn-once marks
  `said_eminence`, `said_scandal` (was `SeatProgressState._said_scandal`, which only this step used), `said_requisition`,
  `said_notice_approach`, `said_confiscation_band`. The relocations are in `sim/tests/equiv_fields.py`. `HouseholdState`'s
  `add_reputation`, `deduct_reputation` and `add_scandal` went (no caller outside one test).
- **`value_weights` is taken in part.** Polity applies `ShiftValueWeight` and publishes `value_weight`, but the dict itself is still
  `Sim.value_weights` (the civilisation's own `values`, saved as `state._weights`): moving it needs edits to `core.py` and
  `saveload.py`, which this task did not own. It is the debt `legacy_value_weights`.
- **The household's answers to the state are the module's, `state_demand.py` is not an engine function module any more.** The
  claims a mod registers for a confiscation (`register_wealth_claims`, `sim.polity.api`) still take the game: the view `provider_game`
  hands it over (the mod contract, read-only for the provider; a debt until a mod can provide the claims as an extension point).
- **Constants moved** (`sim/polity/constants.py`, `grep -c "= declare(" sim/polity/constants.py`): those of the pressure, legitimacy
  and patron-funding mixins; the two priced in labour hours (`EMINENCE_WEALTH_VISIBLE_THRESHOLD`, `STATE_FUNDING_BASE`) are hours there and
  money by `Polity.priced`, and descriptors on `Sim` for readers that remain. Those `core.py` still declares and the year's step reads
  (`SCANDAL_DECAY_RATE`, `EMINENCE_DECAY_RATE`, the bribery and eminence-outcome figures, `REPUTATION_DECAY_TOWARD_FLOOR`, the familiarity
  weights, `REPUTATION_CEILING` in `projects_completion.py`) are read through the keyed view `legacy_constant`.
- **Pure rules moved in** (`git mv`): `eminence_rules`, `state_notice_rules`, `eminence_warning`, `military_rules` (`leverage_of`),
  `value_weight`, `state_demand` (now the claims registry and `describe_stance`); `legitimacy_share` moved from `public_works_rules.py`
  into `rules.py`, with the new rules (alarm, protection, visible scale, familiarity, the scandal warning band, transfer size, the
  levy sum). The patron's grant share is the seats' (`sim.seats.api.patron_grant_share`).

## Mixin classes and files absorbed

| Old class | Old file | Now |
|---|---|---|
| `StatePressureMixin` | `sim/engine/society_state_pressure.py` | `sim/polity/notice.py`, `protection.py`, `eminence.py`, `pressure.py`, `demands.py` (with `state_demand.py`), `constants.py` |
| `LegitimacyMixin` | `sim/engine/legitimacy.py` | `sim/polity/reach.py` |
| `InterestGroupsMixin` | `sim/engine/interest_groups.py` | `sim/polity/groups.py` (the `politics` blocker is the projects start check `group_prohibition`) |
| `TransfersMixin`, `ConcernLevyMixin` | `sim/engine/transfers.py`, `concern_levy.py` | `sim/polity/transfers.py` |
| `ProductionMixin.patron_funding_ask`, `patron_clients`, `state_funding` | `sim/engine/economy_production.py` | `sim/polity/patronage.py` |
| `ActorsMixin.pay_state`, `state_levy_rates`, `state_military_ask` | `sim/engine/society_actors.py` | `transfers.py`, `notice.py` (`state_treasury` stays the cast's: the actors module) |
| `ForwardingPropertiesMixin` reputation, scandal, scandal_last_year, protection, eminence, familiarity | `sim/engine/core_properties.py` | read-only properties in `forward_polity.py` |
| `StepPhasesMixin._step_reputation`, `begin_seat_year` | `sim/engine/core_step_phases.py` | `sim/polity/year.py` (`RenewStanding`, `CloseStandingYear`, the phase) |
| `SocietyMixin` | `sim/engine/society.py` | deleted (it held only `StatePressureMixin`); `BenefactionsMixin` keeps coverage, the working day, colonies and tile ownership |

## State owned

`PolitySeat` (above). Saved with the seat in `seats[id].modules["polity"]`; a handover carries it with the seat.

## Views published

All are `cached=False` today: the module's own figures are written only by its commands, but most views also read the techniques
held, the cast, the purse and the labour market, which other code writes directly.

| View | Kind | Seat | Answers |
|---|---|---|---|
| `standing` | table | yes | reputation, scandal (this and last year), eminence, familiarity, protection, bribes, the answer to the state's demands, concealed wealth, defiance, last withdrawal, governance |
| `eminence` | table | yes | the seat's eminence alone (coin reads it) |
| `state_reach`, `order_reach`, `inspection_reach`, `forest_reach`, `state_authority` | table | no | how far the state's officials, guards, inspectors and foresters reach; its authority is reach worn by consent |
| `visible_scale` | quote | no | how visible a holder's staff, wealth and eminence are to the state |
| `household_scale`, `state_notice` | table | yes | the seat's visible scale, and the state's notice of it |
| `notice_over`, `levy_shares` | quote | no | how far past the notice line a taxpayer stands; the requisition and office it is assessed |
| `military_leverage`, `military_equipment_burden` | table, quote | yes, no | how much of the military branch the founder can put in a patron's hands; the kilograms an equipped soldier costs the state |
| `state_interest`, `alarm_of`, `state_trait_weights` | quote, quote, table | no, yes, no | what the state values in a technique; how alarming it is; the weights |
| `eminence_report`, `confiscation_status`, `state_pressure_report` | table | yes | the screens' reports |
| `interest_groups`, `interest_groups_report` | table | no | the organised groups, and what the state does about each |
| `state_debt`, `patron_funding_ask`, `state_funding` | table | yes | what the state owes; what a patron would give; what the treasury paid |
| `patron_clients` | keyed | no | the playing seats of a country whose techniques run the `state_funding` mechanic |
| `start_gate_group_prohibition` | quote | yes | the start check: a group has the state forbid the node |
| `value_weight` | keyed | no | one of the society's value weights |

## Commands applied

`RaiseScandal`, `AddScandal`, `RecordBribe`, `ScaleProtection`, `ScaleFamiliarity`, `GainReputation`, `AddReputation`,
`SetReputation`, `AddGovernance`, `AnswerStateDemands` (answers what the stance risks), `WithdrawFromPublicLife` (answers (done, text)),
`SettleWithState` (answers (paid, text)), `CarryOutTransfers`, `RenewStanding`, `CloseStandingYear`, `ShiftValueWeight` (answers (before,
after) or a refusal `not_a_value_weight`), and the state's records: `StrikeFromForce`, `SetLandTakenMemory`, `RegisterPeople`,
`SetGrievanceReference`, `ResetStateUnrest`, `SetTileReading`, `RecordRising`, `ReplaceRuler`, `CloseSuccessionDispute`. Their
bridge appliers (in `bridge_campaigns`, `bridge_diffusion`, `bridge_hazards`, `bridge_living_stock`, `bridge_projects`) are deleted.

## Phases

`begin_seat_year` is a `PhaseHook`; its `SHIPPED` entry is `module_seat_phase("begin_seat_year")`. The year's standing inside `seat_work`
is two commands the engine's `_step_reputation` sends around the hours and spending it tallies for other owners.

## Commands sent to other owners

`PayEdge` (ledger), `RecordEvent` (reporting), `ForgetTechnique` (knowledge), `EndRun` (seats).

## Reads

Views of finished modules: `effect_sum`, `effect_values`, `effect_factor`, `effect_best`, `running_mechanics`, `mechanic`,
`patrons_lost_to_eminence`, `techniques_held`, `techniques_granted`, `tree`, `tree_nodes`, `acting_balance`, `transfer_listening`,
`material_pool`, `real_output_per_head`, `output_factor`, `country_world`, `legacy_agent_world`, `legacy_actor_registry`,
`game_random`, `acting_as`, `seat_list`, `seat_country`, `founder`, `automation`, `provider_game`, `cast_recorded`, `government_figures`,
`acting_seat`, `headcount`, `money_per_labour_hour`, `pop_scale`, `population_total`, `running`, `revenue_estimate`, `operating`,
`civilisation`, `year`, `events_enabled`, `money_text`, `mass_text`.

Published by `bridge_polity.py` under the name the owner will publish: `state_treasury` (actors), `standing_floor`, `rep_factor`
(projects), `concern_revenue` (production), `base_annual_wage`, `labour_state_weights` (workforce), `material_substitutes` (materials),
`danger_lines` (the eminence and suspicion figures of the settings). The reach memo is keyed by `techniques_version` (knowledge) and `operating_version` (ventures).
The module reads no `legacy_*` view and no raw object of another owner: the purse is `acting_balance`, the dice are `game_random`,
seats switch with `acting_as`, a seat's country is `seat_country`, a government's grant and levy rates are `government_figures`, and
the told-once mark of the concern levy is the hazards' command `SayOnce`. `provider_game` is the one live object it hands out, to
the mods' wealth-claim readers and seizers.

## Forwarders left (`sim/engine/forward_polity.py`)

The properties `reputation`, `scandal`, `scandal_last_year`, `protection`, `eminence`, `familiarity` (read-only; every write is a command),
`state_trait_weights`, `state_interest`, `alarm_of`, `military_leverage`, `military_equipment_burden_kg_per_soldier_per_year`,
`eminence_report`, `household_scale`, `visible_scale`, `state_notice`, `notice_over`, `levy_shares`, `confiscation_status`,
`state_pressure_report`, `state_authority`, `state_reach`, `order_reach`, `inspection_reach`, `forest_reach`, `interest_groups`,
`interest_groups_report`, `state_debt`, `patron_funding_ask`, `patron_clients`, `state_funding`, `settle_with_state`,
`withdraw_from_public_life`, `carry_out_transfers`, and every declared constant as a class attribute. Callers: the screens, the agents'
world (`agents_port*.py`), the cost and credit mixins, `cause_book.py` and the `bh_cashshelter_z6f2` mod.

## Hard spots, as resolved

- **`Household` (the actor facade in `sim/agents/household.py`) answers `concealed_wealth`, `defiance` and `service_worth` from the
  seat's polity slot** (`_polity`): a debt until the founder's household is served by views like any other actor.
- **Reads that wrote.** `state_reach`'s memo and the banned-materials cache are module attributes, never saved; the cast's state is
  read through `legacy_actors_state` so that no read creates it. The settlement's trial reputation (`SetReputation` set and put back) is
  a write-and-restore that finance must replace with a quote of the credit limit at a stated reputation.
- **Order.** The year's two commands keep the old order: reputation and familiarity, then the hours and spending, then the eminence
  warning, protection, the state's pressure (settling concealment first), the concern levies, scandal decay, eminence, bribery, the two
  warning bands, the denunciation roll and the eminence roll. The equivalence check's micro tier is identical to the base.
- **`GovernanceState` is empty** (its one field moved); the equivalence tool carries the empty section aside
  (`emptied_governance`). Delete the section with the seat state.
