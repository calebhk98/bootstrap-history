# A game does not hold its mods directory

**Status:** open

Mod code operations are per game (`mod_code.operations_of(mods_dir)` is applied by `game_assembly.build`), but which mods directory a
game is over is the process global `sim/engine/bridge_land.MODS_DIR`. `Sim.__init__` reads it once (`core.py`, the `game_assembly.build`
call), and the bridge views that read mod data read it again each time they are asked: `map_overlays` (`bridge_land.py`),
`declared_actor_kinds` (`bridge_actors.py`), `data_store_declarations` (`bridge_stores.py`), `data_command_specs` and
`data_figure_specs` (`bridge_interface.py`). A game answers from its own mods only while the global still names its directory when the
view is first read. The interface and stores modules read theirs while the game is built (`game_assembly.attach`), which is why
`test_mod_operations_smoke` and `test_mod_set_per_game_smoke` can patch `MODS_DIR` around the build alone. The actors' data kinds and the
map overlays are read lazily, so a game built over one directory and asked after the global changed mixes the two. The data loaders
(`data.MODDIR`, `copy_visibility_defaults.MODS_DIRECTORY`, `category_traits.MODS_DIRECTORY`) read the real directory at import, so a data
mod is process-wide whatever the game.

Partly fixed: the `content` module (`sim/content/`) is given the directory by `game_assembly.build` (`OpenContent`) and publishes
`mods_directory`, `installed_mod_ids`, `map_overlays`, `household_need_data`, `declared_actor_kinds` and `data_store_declarations`,
so those answer from the game's own directory and no longer read `bridge_land.MODS_DIR`. Remaining: `data_command_specs` and
`data_figure_specs` (`bridge_interface.py`) still read the global, because validating a declared state path needs `Sim` and the
`@readable` mark (`ui_data.check_state_path`), which the content package may not import; and `Sim.__init__` still reads
`bridge_land.MODS_DIR` to hand to `build`. A bridge view cannot read the module's directory while an assembly is built without a game
(`cli_mods`, `interface_fixture`), so the fix is to move those two views to the interface module with the path check handed in.

Check: `grep -rn "MODS_DIR" sim --include=*.py`. What it would take: `Sim` holds `mods_dir` (set from the constructor, default the
repository's), the bridge views read `sim.mods_dir`, and the data loaders take the directory as an argument from the game that asks.
Until then two games with different data mods in one process are not supported, only different code mods.
