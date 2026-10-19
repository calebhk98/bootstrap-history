# `map` and `move` cannot show place names a mod's map overlay supplies

**Status:** open

The town-table mod (`mods/bh_towns_m8d4`) puts named towns on real tiles as a catalogue of its map overlay and adds
`bh_towns_m8d4:towns` and `bh_towns_m8d4:go`. It cannot make the shipped `map` and `move` screens name them: a mod
may only change their help text (`sim/ui/proto/mod_commands.py:_patch_documentation`), and nothing in those screens
reads a map catalogue for names. A tile is still `China 10` (`sim/geography/tile_names.py:39`, `tile_name`);
`sim/ui/proto/screen_map.py:tile_place` and the `move` rows in `sim/ui/proto/dispatch_labour.py:_cmd_move_base`
build their rows from the tile record alone. `screen_map.py` even tells the player "the data names no towns".
A player who never runs the mod's own commands therefore still cannot see that Texcoco is on the tile they are
leaving, which is Complaints/239 and 289 again.

Why it matters: place names are content, so they should be data a mod or a scenario adds; the screens that choose
a base are the ones that need them.

What it would take: the screens read an optional generic `places` catalogue (`{id, name, tile, rank?}`) from the
merged map and list the names on each tile row. Nothing in the engine would name a town.

Proof of concept: branch `engine-map-place-names` (one commit on `origin/main`, not pushed). It adds
`tile_names.places_on(world_map, tile_id)`, a `places` field on `map` rows and `move` rows only when the map has
places for the tile, and `sim/tests/test_map_place_names.py`. The mod's catalogue is named `towns`; to use the
hook it would be renamed `places` (a one-word data change), after which the shipped screens would show the names
without the player opting in, which is the point of the hook and the reason the rename is held back.
