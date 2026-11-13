# A game does not hold its mods directory

**Status:** closed - a game holds its mods directory (`Sim.mods_dir`, from `Sim(..., mods_dir=)`) and every data table it reads (tree, civilisations, production, needs, trades, technology effects, kits, win-condition labels, units, topic tags, the typed-input name index) is a function of that directory; two games over different directories in one process see their own mods.

A game holds the mods directory it is over (`Sim.mods_dir`, `Sim(..., mods_dir=)`; `bridge_land.MODS_DIR` is only the default when none is
given), and the `content` module publishes it as the `mods_directory` view. What reads it:

- the data loaders: `data.load`, `load_civ`, `civilization_ids`, `node_names`, `nodes_in_civ_money`, the wage helpers (`starting_schedule`,
  `kit_capital`, `schedule_of_civilisation`, `unskilled_numeraire`), `starting_kits`, `win_condition_describe`, and
  `copy_visibility_defaults.table(directory)`;
- the price solver and what feeds it: `prices.default_production_entries(directory)`, `priced_goods_table`, `goods_in_hours`,
  `entries_in_reach`, `numeraire_trade`, `energy_prices.graded`, the opening wage schedule (`build_schedule`, remembered per directory) and
  node revenue; solves over a directory other than the repository's are not persisted to the disk cache (only the committed catalogue is);
- the modules: labour (training, allocation), actors (concern output, site), polity (groups), living stock, markets (every use of a unit's
  mass, the port's production entries, the household model), production (volume, depth, learning), economy goods specs, the prices and
  workforce modules; each declares the `mods_directory` read in its module spec;
- the display layer: `units.registry(directory)`, `topic_tags.current(directory)`, the tree filters, `units_text.for_text`, and the typed-input
  name index (`nodes.names_for(directory)`, one per directory; `parse_typed(line, table, mods_dir)` reads it and the unit words for the game);
- the trade registry, the technology effects, the unit registry, the topic tags and the copy-visibility table are remembered per directory
  and rebuilt when a file under it changes (`sim/content/directory_stamp.py`).

By design the command line, the validators and the offline tools play the repository's own mods: they call `load()`, `load_civ()`,
`civilization_ids()` and the like with no directory, and `STARTING_KITS`, `WIN_CONDITION_LABELS` and the typed-input module defaults are built
over the repository's mods for them. A library function whose `production` or `mods_dir` argument is left out (for example
`demand.production_data()`, `unit_mass.tonnes_per_unit`, `making_cost.cost_of_making`) answers over the repository's mods; every call a game
makes passes the game's. Tests: `sim/tests/test_tables_follow_mods_directory.py` (the tree names, name index, production catalogue, trades,
technology effects, topic tags, unit words and wage schedule of two temporary directories differ, in one process) and
`sim/tests/test_content_tables.py` (the per-directory memo, a changed file giving a new table).
