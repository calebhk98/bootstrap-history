# No hook lets a mod feed deaths or land yield into the year

**Status:** partly done. Hook: `ModCodeApi.externality` (`sim/engine/externalities.py`; tests `test_externalities`, `test_externalities_in_a_game`) feeds deaths by band and a yield factor per tile to land-bound producers. Left: the pooled national farm harvest (`_pooled_farm_weather_multiplier`) is not scaled by tile, and the pollution mod does not register a provider yet.

The industrial pollution mod (`mods/bh_pollution_t9c3`) works out, from the year's producer runs, the smoke, ash,
acid drainage and smelter gas each tile emits, the concentration its people breathe, and the excess deaths and lost
harvest that implies. It cannot make any of that happen. A mod may read engine state but may write only through
documented actor and ledger paths, and no path reaches the two places harm lands:

- Mortality. `Population.step` takes extra deaths only as `epidemic_deaths`, filled in by `disease_year`
  (`sim/engine/core.py:1520`, `sim/world/demography.py:1013`, `sim/engine/disease_port.py:142`). Nothing outside the
  disease package can add to it.
- Land yield. A land-bound producer's yield is `weather` for every producer alike
  (`sim/engine/economy_port_year.py:474`, the `yields` mapping in `_inputs`). No tile-level factor exists.
- `ModCodeApi` offers `command`, `actor_kind`, `policy`, `spawner` and `state` (`sim/engine/mod_code.py:97-121`);
  none of them runs inside the yearly step with a say over those two numbers.

So the mod's command reports `applied_to_the_game: false` on the shipped engine and says what would apply.

Why it matters: smoke, runoff, salted or flooded fields, mine collapse and radiation are all one shape, harm done to
people or land by activity on a tile. Without a general door each such mod either stays a report or needs its own
engine branch (CLAUDE.md 4.3: interventions propagate through normal rules).

Proof of concept: branch `engine-externality-hook` (commit `a5d9ca4e`, not pushed). It adds
`sim/engine/externalities.py`, a registry of providers `(sim, year) -> {"deaths_by_band": {...},
"yield_factor_by_tile": {...}}`; `ModCodeApi.externality(provider)`; adds the providers' deaths to the epidemic deaths
before `Population.step`; and multiplies the weather factor of land-bound producers by the tile's factor in
`_inputs`. With no provider both calls hand back what they were given, so the shipped game is unchanged. Tests:
`sim/tests/test_externalities.py` (registry, quick) and `sim/tests/test_externalities_in_a_game.py` (a provider's deaths
reach `StepFlows`; a tile factor reaches the producers' yields).

Known gaps in the proof of concept: the pooled national farm harvest (`_pooled_farm_weather_multiplier`, the food the
population eats) is not scaled by tile, only the agent economy's land producers; and the providers run twice a year
(deaths, then yields), so a costly provider should cache. Run `python3 -m sim.tests --only externalities,externalities_in_a_game`
on that branch; run the behaviour fingerprint there before relying on it (`python3 -m sim.tests.fingerprint record before.json` on main, then `check before.json`).
