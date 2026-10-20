# A mod cannot make its derived tile towns count in the game

**Status:** partly done. Hook: `ModCodeApi.town_provider` (`sim/labour/town_providers.py`, `sim/tests/test_town_providers.py`). Left: the mod registering its derivation, moving households between tiles, and the urban mortality premium in `Population.step`.

The mod `bh_urbanisation_w2n6` derives a town per land tile from non-farm jobs, food reachable within a haul and
a disease premium (command `bh_urbanisation_w2n6:towns`), as Complaints/closed/107 asks. It can only show the
numbers. The engine's own town size, which the labour market, the `map` screen and every hire reach read, is a
closed formula: `sim/labour/labour_settlement.py` `_town_population_at` (a nominal reference size scaled by the
tile's place in the nation, capped at `TOWN_MAX_SHARE_OF_TILE` of the tile's people, itself a temporary heuristic).
`ModCodeApi` (`sim/engine/mod_code.py`) offers commands, actor kinds, policies and spawners, none of which can
replace that estimate, so a derived town can never change hiring pools, market size or the founder's reach.

Why it matters: CLAUDE.md 4.1 wants city size to fall out of food, jobs and mortality. Until a model can supply
the town, the fixed formula stays the only town the game uses, and a mod's town table (this one or
`bh_towns_m8d4`) stays a report beside the game rather than part of it.

Not covered even by the proof of concept: moving households between tiles, and applying the urban mortality
premium to the demography module's deaths (`sim/world/demography.py`, `Population.step` takes one national
disease burden). Both need hooks of their own.

Proof of concept: branch `engine-town-population-provider` (commit 5813f414). It adds
`sim/labour/town_providers.py` (a registry of `function(labour, tile, nominal_people) -> people or None`),
exports `register_town_provider` from `sim/labour/api.py`, makes `_town_population_at` ask the providers first
(the answer is bounded by the tile's own people, so a town never exceeds the nation), and adds
`ModCodeApi.town_provider(name, function)` so mod code registers one under its namespace. The regression test
is `sim/tests/test_town_providers.py` (no provider leaves the nominal town; a provider sets it and `None`
declines; the bound by the tile's people). With it the mod's `towns` derivation could be registered as the
provider; that last step is not made on the mod branch because the mod must leave the shipped game unchanged.
