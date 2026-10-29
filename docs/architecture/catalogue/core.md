# `Sim` after the move: the composition root and what dissolves

**Status:** draft, task 1.5, analysis of `e8b004c`. Not a module: it lists what stays in `Sim` and what the migration deletes. `Sim` has 62 direct bases today (`python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(len(Sim.__bases__))"`).

## What stays

Per `MODULE_REGISTRY_PLAN.md` 4.7: the state, the random source, the seats and `act_as`, the year loop over phases, and the assembled modules. The methods the analysis assigns to the root, with how many references from modules go to each:

| Method or property | Defined in | References from modules | Fate |
|---|---|---|---|
| `__init__` | `Sim` | 0 | stays: builds state, then asks the assembly |
| `_active_changed` | `EconomyMixin` | 0 | deleted: `StartProject`/`StopProject` bump `active` |
| `_done_changed` | `EconomyMixin` | 7 | deleted: each write is a command that bumps the `done` channel |
| `_done_memo` | `MaterialSupplyMixin` | 4 | deleted: a hand-built stamp cache; replaced by view versions |
| `_new_facade` | `SeatMixin` | 0 | stays (seat facades) or folds into `ledger` rebind |
| `_operating_changed` | `EconomyMixin` | 1 | deleted: `SetOperating` bumps the `operating` channel |
| `_producers_memo` | `MaterialSupplyMixin` | 2 | deleted: same |
| `_reconnect_state_hooks` | `Sim` | 0 | deleted with the invalidating containers |
| `_reset_active` | `EconomyMixin` | 0 | deleted with the version counters |
| `_reset_economic_caches` | `EconomyMixin` | 1 | becomes `assembly.rebind(state)` on load and seat switch (task 1.2) |
| `_reset_operating` | `EconomyMixin` | 0 | deleted with the version counters |
| `_reset_workforce` | `EconomyMixin` | 0 | deleted with the version counters |
| `_run_seat_work` | `StepPhasesMixin` | 0 | becomes the phase `seat_work`, whose sub-steps belong to `projects`, `materials`, `ventures` |
| `_shared_answer` | `ViewShareMixin` | 0 | deleted (ViewShare) |
| `_shared_bill` | `ViewShareMixin` | 1 | deleted (ViewShare) |
| `_shared_bill_keys` | `ViewShareMixin` | 0 | deleted (ViewShare) |
| `_standalone_stamp` | `ViewShareMixin` | 0 | deleted (ViewShare) |
| `_switch_seat` | `SeatMixin` | 1 | stays inside `act_as` |
| `_view_world_stamp` | `ViewShareMixin` | 0 | deleted (ViewShare) |
| `_workforce_changed` | `EconomyMixin` | 0 | deleted: workforce commands bump `workforce` |
| `_wrap_seat_containers` | `Sim` | 1 | deleted with the invalidating containers |
| `act_as` | `SeatMixin` | 13 | stays: the only switch; ends with `bump_seat(seat)` |
| `add_seat` | `SeatMixin` | 1 | stays as the root's seat registry; the module slots are created by assembly |
| `begin_seat_year` | `StepPhasesMixin` | 0 | becomes the phase of the same name; its body is split by module |
| `begin_world_year` | `StepPhasesMixin` | 0 | becomes the phase of the same name |
| `close_view_scope` | `ViewShareMixin` | 0 | deleted (ViewShare) |
| `open_view_scope` | `ViewShareMixin` | 0 | deleted (ViewShare) |
| `run` | `Sim` | 0 | stays |
| `step` | `Sim` | 0 | stays: the year loop |
| `sync_seat_facades` | `SeatMixin` | 0 | stays |
| `year` | `ForwardingPropertiesMixin` | 9 | stays: `state.scenario.year`; every module reads the year from the clock |

## What dissolves

1. **`ForwardingPropertiesMixin`** (`sim/engine/core_properties.py`, 165 methods as getter and setter pairs, 83 distinct names): aliases that give a field two names (`sim.capital` and `sim.state.household.capital`). Each alias disappears; the readers use the owner's view and the writers its command. The name-to-module table:

| Alias | Module | Referenced from other modules |
|---|---|---|
| `_dashboard_history` | `reporting` | 0 |
| `_founder_death_aged` | `seats` | 0 |
| `_founder_death_year` | `seats` | 0 |
| `_last_buy_refusal` | `reporting` | 0 |
| `_material_demand_cache` | `materials` | 0 |
| `_said_command_index` | `reporting` | 0 |
| `_said_parallelism` | `reporting` | 0 |
| `_said_scandal` | `reporting` | 0 |
| `_said_stack_caution` | `reporting` | 0 |
| `active` | `projects` | 0 |
| `artisans` | `workforce` | 0 |
| `binding` | `materials` | 0 |
| `bondage_debt` | `finance` | 0 |
| `bondage_years_left` | `finance` | 0 |
| `bountied` | `projects` | 0 |
| `bounties_paid` | `projects` | 0 |
| `capital` | `ledger` | 4 |
| `contract_hours` | `workforce` | 0 |
| `credit_frozen_until` | `finance` | 0 |
| `dead_reason` | `seats` | 0 |
| `directors_extra` | `workforce` | 0 |
| `done` | `knowledge` | 0 |
| `done_year` | `knowledge` | 1 |
| `eminence` | `polity` | 0 |
| `employees` | `workforce` | 0 |
| `failed_attempts` | `projects` | 0 |
| `familiarity` | `polity` | 0 |
| `farm_hectares` | `agriculture` | 0 |
| `farm_stock_kg` | `agriculture` | 6 |
| `fog` | `knowledge` | 4 |
| `forest_ha` | `resources` | 1 |
| `forgotten` | `knowledge` | 0 |
| `founder_alive` | `seats` | 0 |
| `freedmen` | `workforce` | 0 |
| `fuzzy_estimates` | `knowledge` | 0 |
| `goal` | `seats` | 11 |
| `goal_year` | `seats` | 0 |
| `granted` | `knowledge` | 0 |
| `hour_allocations` | `workforce` | 0 |
| `hours_this_year` | `workforce` | 1 |
| `insolvent_years` | `finance` | 0 |
| `interest_paid` | `finance` | 0 |
| `last_settlement` | `finance` | 0 |
| `last_taught` | `workforce` | 0 |
| `life_left` | `seats` | 0 |
| `log` | `reporting` | 2 |
| `manumitted_total` | `workforce` | 0 |
| `mine_tranches` | `resources` | 0 |
| `mines` | `resources` | 0 |
| `money_real` | `reporting` | 1 |
| `mothballed` | `ventures` | 0 |
| `nitre_bed_m2` | `resources` | 0 |
| `operating` | `production` | 0 |
| `output_factor` | `hazards` | 1 |
| `paid_towards` | `projects` | 0 |
| `policy` | `seats` | 4 |
| `pop_children` | `demography` | 0 |
| `pop_elderly` | `demography` | 0 |
| `pop_working_age` | `demography` | 0 |
| `protection` | `polity` | 0 |
| `reputation` | `polity` | 0 |
| `revealed` | `knowledge` | 0 |
| `scandal` | `polity` | 1 |
| `scandal_last_year` | `polity` | 2 |
| `scholars` | `workforce` | 0 |
| `shortages` | `materials` | 0 |
| `shut_for_staff` | `ventures` | 0 |
| `slaves` | `workforce` | 0 |
| `spend_last_year` | `ledger` | 0 |
| `teaching_hours_this_year` | `workforce` | 0 |
| `throttle` | `materials` | 0 |
| `trade_hours_used` | `workforce` | 0 |
| `trade_introduced_year` | `workforce` | 0 |
| `trade_schools` | `workforce` | 0 |
| `trades_created` | `workforce` | 0 |
| `trades_endemic` | `workforce` | 0 |
| `training` | `workforce` | 0 |
| `wage_hours_this_year` | `workforce` | 0 |
| `wages_earned` | `workforce` | 0 |
| `wages_prepaid` | `workforce` | 0 |
| `work_trade` | `workforce` | 0 |
| `worker_housing_places` | `workforce` | 0 |
| `year` | `core` | 9 |

2. **The port mixins** (`LabourPortMixin.labour`, `GeographyPortMixin.geography/world_map`, `EconomyPortMixin.economy`, `DiseasePortMixin`): lazy properties that hand a package the whole `Sim` through an adapter. They become declared view lists; see `caches_and_ports.md`.
3. **`ViewShareMixin`** (was `sim/engine/view_share.py`): a hand-made version-stamp cache, now the `sharing` module (`sim/sharing/`), whose stamp reads only views.
4. **`EconomyMixin`'s cache methods** (`economy.py:221-274`): the `_done_seq` memo, the four `*_changed` hooks, `_reset_economic_caches`.
5. **Empty shells**: `SocietyMixin`, `BenefactionsMixin` and `ProjectsMixin` define no methods of their own (see the placement table in the README, methods 0); they simply leave the base list.

## References to and from the root

41 references go to the root's methods from modules (listed above by method). The commonest are the clock (`year`: from `hazards`, `disease`, `polity`, `seats`, `finance`) and the cache hooks that are deleted; `year` becomes a read of the clock every module is handed.

