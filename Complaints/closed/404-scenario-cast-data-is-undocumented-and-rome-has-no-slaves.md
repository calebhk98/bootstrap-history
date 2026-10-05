# The `"cast"` key a scenario uses to declare countries, players and strata is undocumented, and no civilisation declares its slaves

**Status:** closed - bonded strata work and their keeper is paid for it (sim/tests/test_agents_strata.py, sim/tests/test_rome_slave_stratum.py); the cast-key and foreign-economy documentation items remain listed below as follow-ups in the mod loader and schema docs

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

## Sourced share, now applied

`rome_100ad.json` declares a bonded `slaves` stratum at the sourced share (Scheidel 2005, confidence C), naming the trade `labourer`. A bonded stratum with a trade now records the value of its year of work at the going pay of that trade, and the keeper stratum is credited it at settlement beside paying the keep (`sim/agents/stratum_year.py`, `bonded_product` and `settle_keep`). The bonded are part of the population the economy already counts as hands, so their wage bill was already paid by employers and previously reached no stratum; the credit attributes it to the owner and mints nothing beyond the `edge:economy` bridge every free stratum already uses. Measure with `PYTHONPATH=. python3` on the Rome opening as in `sim/tests/test_rome_slave_stratum.py`.
