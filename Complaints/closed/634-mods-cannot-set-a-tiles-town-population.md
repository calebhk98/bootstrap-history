# A mod cannot make its derived tile towns count in the game

**Status:** closed

**What is wrong.** The mod `bh_urbanisation_w2n6` derives a town per land tile from non-farm jobs, food reachable within a
haul and a disease premium (command `bh_urbanisation_w2n6:towns`), as `Complaints/closed/107` asks, but only shows the
numbers. CLAUDE.md 4.1 wants city size to fall out of food, jobs and mortality; until the mod's town is the one the game
uses, the nominal formula in `_town_population_at` (`sim/labour/labour_settlement.py`; a nominal reference size scaled by the
tile's place in the nation, capped at `TOWN_MAX_SHARE_OF_TILE`, a temporary heuristic) stays the only town.

**Done in main.** `ModCodeApi.town_provider(name, function)` (`sim/engine/mod_code.py`) registers
`function(labour, tile, nominal_people) -> people or None` through `sim/labour/town_providers.py` (exported from
`sim/labour/api.py`); `_town_population_at` asks the providers first and bounds the answer by the tile's own people.
Tests: `sim/tests/test_town_providers.py`.

**Left.**

- The mod does not register its `towns` derivation as a provider: the mod must leave the shipped game unchanged without
  consent, so the registration has to sit behind the mod's own gate. Check with `grep -n town_provider mods/bh_urbanisation_w2n6/*.py`.
- Moving households between tiles: `ModEffects.move_people` exists (`sim/engine/mod_effects.py`); whether it fits a
  per-tile migration is not tried (see 639).
- The urban mortality premium: `Population.step` (`sim/world/demography.py`) takes one national disease burden, and
  `kill_people` takes a country and a share, not a tile (see 639; 635's externality hook feeds deaths by band, not by tile).

## Done

- The mod registers its derivation. `bh_urbanisation_w2n6` (`mods/bh_urbanisation_w2n6/hooks.py`) declares tile stores
  `town_people` and `urban_mortality_premium`, a world phase `derive_towns` (after `money_world`) that stores each tile's
  derived values, and `api.town_provider("towns", ...)` reading the stores. It is behind the mod's consent like all mod
  code. Until the first phase has run the provider has no opinion. Test: `sim/tests/test_urbanisation_mod_scenario.py`.
- The urban mortality premium reaches `Population.step` as `urban_mortality_premium` (a share of the baseline death
  rate of every band, `sim/world/demography.py`). `api.town_provider(..., mortality_premium=...)` registers it
  (`sim/labour/town_providers.py`); `SettlementMixin.town_mortality_premium_by_tile` averages it over the tile's people and
  `step_regions` passes it per region. No number is typed in the engine: the figure is the mod's own labelled heuristic
  (`URBAN_DISEASE_PREMIUM_AT_FULL_CROWDING`, with its retire text). Tests: `sim/tests/test_urban_mortality_premium.py`.
- Moving households between tiles: not built, by decision. The engine has one migration rule
  (`sim/labour/regional_migration.py`: working-age people move toward better-fed bordering tiles) and a town cannot
  exceed its tile's people, so a second jobs-driven rule would duplicate it with no source. `ModEffects.move_people`
  moves people between strata, not tiles, so it does not fit either (639). If towns should pull migrants, that is a
  change to the one rule, filed as its own complaint.
