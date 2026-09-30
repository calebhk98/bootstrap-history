# Dead functions, unused classes and a large unlabelled-to-player heuristic backlog

**Status:** open

The code inventory lists functions with no live caller, including `MineWorking`, `capacity_reserves`, `Commodities.on_hand`, `working_age_population`, `consumers_of`, `joint_output_value_shares_for_recipe`, `pack_animals_required_for_daily_delivery`, `shafts_needed_fractional`, `adjusted_tightness_factor`, `granary_projection`, and several helpers in `state.py`; `aggregate_household_demand_all_goods` has no caller. It also counts ~885 `declare()`d constants, ~714 tagged `temporary_heuristic` and 3 `hardcoded_outcome`.

Note: the dead-caller list is from one agent's reading and not individually re-verified; confirm each with `python3 sim/pylint_blind_spots.py` or grep before deleting.

What it would take: delete confirmed-dead code; publish the heuristic burndown with `python3 sim/code_health.py`.

Found by a code inventory made for the new-player playtest (`playtest_notes/code_systems_inventory.md`); each claim below was re-checked by grep.
