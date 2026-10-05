# The `"cast"` key a scenario uses to declare countries, players and strata is undocumented, and no civilisation declares its slaves

**Status:** partly - cast, bondage fields and foreign economies documented; a sourced share exists (below) but bonded strata supply no labour yet, so adding it would make Rome worse; the mod loader item is in mods/TASKS.md

A game's roster is seeded once and saved (`ActorsState.cast`, `ActorsState.countries`; see
`sim/agents/MULTIPLAYER.md`). It is built from:

- the civilisation played;
- the foreign economies enabled for the year (`data/world/foreign_economies.json`);
- an optional `"cast"` key in a civilisation file (`sim/agents/cast.py`). The key may hold
  `strata`, `countries`, `actors`, `treasury` and `location`.

Mods already patch civilisation files, so the key works for mods. These parts are still missing:

- `data/civilizations/_SCHEMA.md` does not document `"cast"`.
- `mods/README.md` does not list `data/world/foreign_economies.json` as mod data, so a mod cannot add
  a trading partner.
- No civilisation file states an enslaved population. The default strata split
  (`sim/agents/strata_seed.py`) adds a bonded stratum only when `debt_bondage` or `bondage_years` is
  set, and `rome_100ad.json` sets neither. A Rome start therefore has no slaves, although their share
  of the population is an initial condition the data may state (CLAUDE.md 4.1).
- `docs/architecture/README.md` does not link `sim/agents/MULTIPLAYER.md`.

What it would take:
- Document the key.
- Give `rome_100ad.json` (and any civilisation with chattel slavery) a `"cast": {"strata": [...]}`
  entry or a population share field the default split reads, sourced.
- Add the foreign-economy file to the mod loader.

## Sourced share, held back

Scheidel, "Human Mobility in Roman Italy II: The Slave Population", JRS 95 (2005) 64-79: about a tenth of the empire's people were enslaved (plausible range roughly 8-15%), Italy and the cities higher; the older third-or-more figure for Italy is unsupported. Confidence C.

A trial cast for `rome_100ad` with a bonded `slaves` stratum at that share (owner `rich`) ran without engine changes, but bonded strata only consume through the owner's keep: they add no hours to the labour supply, so a tenth of Rome stopped producing and the rich stratum ran deeply negative in the opening year. Adding the share waits until bonded people work (their hours enter the labour market on the owner's account). Branch `rome-slave-stratum-and-weather-seed` holds the trial data and its test.
