# The mine labour-hours profile cache is shared by every game and ignores the map

**Status:** closed - the cache is removed (an uncached call is about a millisecond); the unkeyed historical-rates cache is removed too

`_PROFILE_CACHE` in `sim/resources/costs.py` (the class attribute `_MINE_PROFILE_CACHE` of `MiningMixin` before the move) is keyed
by (material, the running works' effects) only. It is one table for the process, so two games in one process, or a mod that
changes the deposit data or the map's metals, read each other's labour hours per tonne: `mine_labour_hours_per_tonne` depends on
`deposit_model.metals(world_map)` and `load_deposits`. Evidence: the key built in `labour_hours_per_tonne` has no map or
data identity. Kept as it was in the move (behaviour must not change); the fix is to key it on the map (as
`catalogue.works_priced_materials` does with `lru_cache` on the map) or to hold it on the module, which `setup()` already rebuilds per game.
