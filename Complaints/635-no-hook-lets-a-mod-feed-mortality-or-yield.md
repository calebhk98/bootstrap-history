# No hook lets a mod feed deaths or land yield into the year

**Status:** partly - the hook is in main (`ModCodeApi.externality`); the pollution mod registers a provider; left: the pooled national farm harvest is not scaled by tile

**What is wrong.** The industrial pollution mod (`mods/bh_pollution_t9c3`) works out, from the year's producer runs, the
smoke, ash, acid drainage and smelter gas each tile emits, the concentration its people breathe, and the excess deaths and
lost harvest that implies. Smoke, runoff, salted or flooded fields, mine collapse and radiation are all one shape, harm done
to people or land by activity on a tile (CLAUDE.md 4.3: interventions propagate through normal rules). The mod
registers its provider (`externalities` in `mods/bh_pollution_t9c3/hooks.py`).

**Done in main.** `ModCodeApi.externality(provider)` (`sim/engine/mod_code.py`) registers a provider
`(sim, year) -> {"deaths_by_band": {...}, "yield_factor_by_tile": {...}}` in `sim/engine/externalities.py`. The providers'
deaths are added to the epidemic deaths before `Population.step`, and the tile's factor multiplies the weather factor of
land-bound producers. With no provider both hand back what they were given. Tests: `sim/tests/test_externalities.py`,
`sim/tests/test_externalities_in_a_game.py`.

**Left.**

- The pooled national farm harvest (`_pooled_farm_weather_multiplier`, the food the population eats) is not scaled by
  tile, only the agent economy's land producers. Find it with `grep -rn "_pooled_farm_weather_multiplier" sim`.
- Providers run twice a year (deaths, then yields), so a costly provider should cache.
- Before relying on it, run the behaviour fingerprint (`python3 -m sim.tests.fingerprint record before.json` on the
  parent, then `check before.json`).
