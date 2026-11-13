# The opening wage schedule differed by a few parts in a billion depending on which caller solved the prices first

**Status:** closed - a mods directory that holds the repository's catalogue yields the default catalogue object, so the solve stops at one tolerance

`sim/prices/prices.py` `solved_prices_at_wages` stops at the engine tolerance when `production_entries` is the default
object (`_DEFAULT_PRODUCTION_ENTRIES`) and at the solver's own tight tolerance otherwise, and its in-process cache key
does not hold that choice. `default_production_entries(mods_dir)` returned the cached catalogue of a named directory
without setting the default object, so `data.kit_capital` and `data.starting_schedule` (which name the mods directory)
solved tight whenever the default had not yet been loaded, while `wage_schedule.build_schedule` with no directory solved
loose. Whichever solved first filled the cache. After a topic that clears the caches (`engine_prices_rule`), the quick
tier gave `test a kit is labourer years of the opening wage` and `test kit money follows the coin` different figures
(a relative difference near 4e-9) from the same topic run alone.

Reproduce before the fix: `python3 -m sim.tests --only engine_prices_rule,wage_floor_and_coin_standard --jobs 1`.

Fix: `default_production_entries` returns the default object when the named directory's catalogue is the repository's.
Regression test: `sim/tests/test_default_production_entries_identity.py` (either call order gives the default object).
