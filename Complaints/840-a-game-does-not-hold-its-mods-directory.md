# A game does not hold its mods directory

**Status:** partly - a game holds its mods directory (`Sim.mods_dir`) and the data loaders, trade and technology tables take it; the price solver, the world data loaders (production, needs, units, tags) and the typed-input name index still read the repository's mods

Mod code operations are per game (`mod_code.operations_of(mods_dir)` is applied by `game_assembly.build`), but which mods directory a
game is over is the process global `sim/engine/bridge_land.MODS_DIR`. `Sim.__init__` reads it once (`core.py`, the `game_assembly.build`
call), and the bridge views that read mod data read it again each time they are asked: `map_overlays` (`bridge_land.py`),
`declared_actor_kinds` (`bridge_actors.py`), `data_store_declarations`. A game answers from its own mods only while the global still names its directory when the
view is first read. The interface and stores modules read theirs while the game is built (`game_assembly.attach`), which is why
`test_mod_operations_smoke` and `test_mod_set_per_game_smoke` can patch `MODS_DIR` around the build alone. The actors' data kinds and the
map overlays are read lazily, so a game built over one directory and asked after the global changed mixes the two. The data loaders
(`data.MODDIR`, `copy_visibility_defaults.MODS_DIRECTORY`) read the real directory at import, so a data
mod is process-wide whatever the game.

Fixed: the `content` module (`sim/content/`) is given the directory by `game_assembly.build` (`OpenContent`) and publishes
`mods_directory`, `installed_mod_ids`, `map_overlays`, `household_need_data`, `declared_actor_kinds` and `data_store_declarations`; the
category traits and the interface module's command and figure files answer from it. `Sim.__init__` reads `bridge_land.MODS_DIR` once into
`Sim.mods_dir` and hands that to `build`, `default_policy(manual, mods_dir)` (the policy switches mods add, for the first seat and for
`register_seat`) and nothing else asks the global; `node_rederive` and `opening_money` build the wage schedule from the game's
`trade_records` view, not the import-time registry. Tests: `sim/tests/test_default_policy_mods_dir.py`,
`test_mod_set_per_game_smoke`.

Fixed: the trade registry, the technology effects and the starting wage tables are no longer import-time tables of `sim/engine/data.py`
(`TRADE_REGISTRY`, `TRADE_NOTES`, `TRADES_ABSENT`, `TRADE_FAMILY`, `TECH_EFFECTS`, `WAGES`, `ANNUAL_WAGE`, `MONEY_PER_LABOUR_HOUR` and
`trade_family` are gone; nothing re-exports them). Every reader holding a game answers from the game's `content` views: the trade
commands and screens (`ui/proto/dispatch_labour`, `dispatch_ventures`, `economy`, `ui/market_report`), `path_search`, `fuzzy_estimates` and the
save check (`saveload._check_save_trade_name_sets` takes the game's trade ids). `kit_capital`, `schedule_of_civilisation`,
`unskilled_numeraire` and `starting_schedule` take a `mods_dir`; the game's opening purse and its scenario source pass `Sim.mods_dir`. The unused
`StepContext.trade_family` is removed. Tests that hold no game read the repository's own tables from `sim/tests/repository_tables.py`.
Test: `sim/tests/test_content_tables.py` (`TwoDirectoriesTwoTables`: two directories give two trade registries and two tech-effect tables).

Also fixed: `data.load`, `load_civ`, `civilization_ids`, `node_names`, `nodes_in_civ_money`, `goods_provenance`, `calculated_goods_prices`,
`starting_schedule`, `kit_capital`, `starting_kits` and `win_condition_describe` take a `mods_dir` (the repository's when none is named);
`copy_visibility_defaults.table(mods_directory)` replaced the module constant `MODS_DIRECTORY`; `Sim(..., mods_dir=)` takes the directory
(`bridge_land.MODS_DIR` is only the default when none is given) and builds its civilisation, kit capital, node money and tree views over it;
the goal screens and the seat kit check read the game's `mods_directory` view. The trade registry, the tech-effects table and the
copy-visibility table are remembered per directory and rebuilt when a file under it changes (`sim/content/directory_stamp.py`; tests in
`test_content_tables.py`).

Left (a game over another directory still reads the repository's mods in these):
- The price solver and the economy's data: `sim/engine/validate_production.load_production` (the solver's door, `sim/prices/engine_seam.py`),
  `sim/world/demand.py`, `sim/world/need_demand.py`, `sim/workforce/wage_schedule.py` (`load_needs(REPOSITORY_ROOT)`),
  `sim/engine/units.py` (`load_units()` default registry), `sim/engine/topic_tags.py` and `sim/prices/solve_cache.py` (keyed on the repository's
  `mods`) load production, needs, units or tags from the repository root's `mods`. `load(mods_dir)` still prices goods through the solver, so a
  data mod to production in another directory is not seen by prices.
- The typed-input name index `sim/ui/proto/nodes.py` (`NODE_IDS`, `NODE_NAME_NORM`, built once from `node_names()` because `parse_typed` has
  no `Sim`), and the command line's `STARTING_KITS` and `WIN_CONDITION_LABELS` constants.
- The command line (`ui/cli*`, `path_search`, `planner`, `baseline_game`, the tools) builds games over the repository's mods by calling
  `load()` and `load_civ()` without a directory; that is the repository's own directory by design, until the command line takes a mods option.
What it would take: the price solver and the world data loaders take the directory from the game that asks (a handful of packages), and
`parse_typed` takes the game so the name index is per game.

Check: `grep -rn "MODS_DIR\|MODDIR" sim --include=*.py`. Until the items above move, two games with different data mods in one process are not supported for production, needs and units data, only for the trade, technology and tree tables and different code mods.
