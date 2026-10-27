# The map's list of tile-store layers names only the base game's stores

**Status:** closed - `screen_map` reads `sim.stores.declared()`; `mod_stores.DECLARED`, `TILE` and `tile_layer` are gone

`sim/ui/proto/screen_map.py` (the unknown-layer reply of `map`) lists the layers it offers from `mod_stores.DECLARED`. The declared
stores are now a game's own (the stores module's `store_declarations` point), so that dictionary holds the base game's stores only
(`sim/engine/mod_stores.py`); a mod's tile store is still shown by `{"cmd":"map","layer":"<mod>:<store>"}` (it goes through
`sim.stores.tile_layer`) but is missing from the `choices` of the refusal for a layer that does not exist.

Fix: in `screen_map.map_screen` build the choices from `sim.stores.declared()` (a dictionary of `StoreSpec`) and delete
`mod_stores.DECLARED`, `mod_stores.TILE` and `mod_stores.tile_layer`. The one-line edit was left because `sim/ui/` was being edited by
another branch. No test pins the choices of a mod's store; add one with the fix.
