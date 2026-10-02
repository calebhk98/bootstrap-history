# Dead functions, unused classes and a large unlabelled-to-player heuristic backlog

**Status:** closed - dead code removed, burndown recorded below

The code inventory lists functions with no live caller, including `MineWorking`, `capacity_reserves`, `Commodities.on_hand`, `working_age_population`, `consumers_of`, `joint_output_value_shares_for_recipe`, `pack_animals_required_for_daily_delivery`, `shafts_needed_fractional`, `adjusted_tightness_factor`, `granary_projection`, and several helpers in `state.py`; `aggregate_household_demand_all_goods` has no caller. It also counts ~885 `declare()`d constants, ~714 tagged `temporary_heuristic` and 3 `hardcoded_outcome`.

Note: the dead-caller list is from one agent's reading and not individually re-verified; confirm each with `python3 sim/pylint_blind_spots.py` or grep before deleting.

What it would take: delete confirmed-dead code; publish the heuristic burndown with `python3 sim/code_health.py`.

Found by a code inventory made for the new-player playtest (`playtest_notes/code_systems_inventory.md`); each claim below was re-checked by grep.

## Resolution

Re-checked on the current code by grep over sim, data, mods and tools, with no getattr, dispatch-table or mod access to any of them. Removed: `MineWorking`, `capacity_reserves`, `Ledger.on_hand` (the class the complaint calls `Commodities.on_hand`), `Population.working_age_population`, `consumers_of`, `joint_output_value_shares_for_recipe`, `pack_animals_required_for_daily_delivery`, `granary_projection`, `aggregate_household_demand_all_goods`, and the tests that covered only them. `sim/tests/test_dead_code_removed.py` keeps them gone.

Not dead, kept: `shafts_needed_fractional` (called by `shafts_needed` and the labour-cost helper in `deposits.py`) and `adjusted_tightness_factor` (called from `wages.py`). The "helpers in `state.py`" have callers (`sim/engine/state.py` and `sim/ui/proto/state.py` were both checked).

Heuristic backlog: the count has fallen since the inventory (the ~200 unread constants were removed). Current figures come from `python3 sim/constants.py --burndown`: 715 declared, 531 `temporary_heuristic` (74.3%), 3 `hardcoded_outcome`. Re-run the command for today's numbers; they change with every merge.
