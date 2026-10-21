# A mod cannot make its derived tile towns count in the game

**Status:** partly - the hook is in main (`ModCodeApi.town_provider`); left: the mod registering its derivation, moving households between tiles, and the urban mortality premium in `Population.step`

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
