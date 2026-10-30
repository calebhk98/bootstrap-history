# A game does not hold its mods directory

**Status:** partly - a game holds its mods directory (`Sim.mods_dir`) and its assembly, policy defaults and opening repricing read it; the engine's import-time data tables below still read the repository's mods

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

The trade registry, the technology effects and the foreign economies are loaded twice, from the same files: the engine's
import-time constants (`data.TRADE_REGISTRY`, `TRADE_NOTES`, `TRADES_ABSENT`, `TRADE_FAMILY`, `TECH_EFFECTS`, `WAGES`) read
`data.MODDIR`, and the `content` module's views (`trade_records`, `trade_notes`, `trades_absent`, `trade_family`, `tech_effects`,
`foreign_economy_records`, `not_traded_materials`) read the directory the game was given. For a game built over another directory the
engine's constants and the views disagree; code that still reads the constants (`ui/proto`, `path_search`, `saveload`, `fuzzy_estimates`,
`opening_money`, `node_rederive`) sees the repository's mods. The loaders are plain functions of a directory (`sim/content/trades.py`,
`tech_effects.py`, `foreign_economies.py`), so the fix is to move those readers to the views. Left: the readers of the constants listed
above other than the two moved (`ui/proto/dispatch_*`, `economy`, `market_report` and `path_search` import `WAGES`, `TRADE_FAMILY`, `TRADE_NOTES`
and `TRADES_ABSENT` at import and have no game in hand at the module level; `saveload` and `fuzzy_estimates` read `WAGES`; `data.py` builds
the tree, civilisations, production, kits and win-condition labels from `MODDIR` at import and `load`/`load_civ` are called before a `Sim`
exists, so the tree a game is given is the repository's mods' tree), and `copy_visibility_defaults.MODS_DIRECTORY`, which `data.load` applies
to the tree it loads.

Check: `grep -rn "MODS_DIR" sim --include=*.py`. What it would take: the `Sim` constructor takes the directory (today it reads `bridge_land.MODS_DIR`) and the data loaders take the directory as an argument from the game that asks.
Until those move two games with different data mods in one process are not supported, only different code mods.
