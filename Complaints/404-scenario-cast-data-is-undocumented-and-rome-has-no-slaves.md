# The `"cast"` key a scenario uses to declare countries, players and strata is undocumented, and no civilisation declares its slaves

**Status:** open

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
