# A game does not hold its mods directory

**Status:** partly - a game holds its mods directory (`Sim.mods_dir`); its assembly, policy defaults, opening repricing, trade and technology tables and trade screens read it; `data.load`/`load_civ` (tree, civilisations, production, kits) and `copy_visibility_defaults` still read the repository's mods

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

Left: `data.py` builds the tree, civilisations, production catalog, starting kits and win-condition labels from `MODDIR` at import or in
`load`/`load_civ`, which are called before a `Sim` exists, so the tree and civilisation a game is given are the repository's mods'; the
registry-dependent steps inside `load` (node revenue over `unskilled_numeraire()`, the wage schedule) therefore still use `MODDIR` by
default. `copy_visibility_defaults.MODS_DIRECTORY`, which `data.load` applies to the tree it loads, is the same. `Sim.__init__` still reads
`bridge_land.MODS_DIR` once. What it would take: `load(mods_dir)`, `load_civ(name, mods_dir)` and the callers that build a `Sim`
(`ui/cli*`, `simulator.py`, `path_search`, the tests' harness) pass the directory down; then the global goes.

Check: `grep -rn "MODS_DIR" sim --include=*.py`. What it would take: the `Sim` constructor takes the directory (today it reads `bridge_land.MODS_DIR`) and the data loaders take the directory as an argument from the game that asks.
Until those move two games with different data mods in one process are not supported, only different code mods.
