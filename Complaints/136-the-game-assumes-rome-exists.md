# The game assumes Rome exists

**Status:** partly - the game starts and steps with the default civilisation's file absent (sim/tests/test_civilisation_independence.py); no code names a civilisation id; the default comes from `default_civ`, falling back to the first civilisation present.

Remains: land is hectares inside `sim/world/land.py` (the allocation, yield,
intensity and rent functions; `RegionLand.arable_hectares`), and node money is
labour hours (`Complaints/144`). The production data still names land in
iugera (`iugerum_land`, `land_iugera_years`), and the price solver converts at
that one edge (`Complaints/282`). Most engine messages still spell the money
word "denarii" and are swapped for the civilisation's own word at the display
edge (`sim/engine/proto/util.py`); comments and tests that say "Rome" as a
calibration baseline remain. Measure with
`grep -rEoi "denari|iuger" sim/engine sim/world --include=*.py | wc -l` and
`grep -rEoi "roman|\brome\b" sim/engine sim/world --include=*.py | wc -l`.
Tests still use Rome as the default fixture.

Every civilisation should be one data file that the rest of the game does not
depend on. Rome is not: deleting `data/civilizations/rome_100ad.json` stops
the game from starting even when another civilisation is chosen (the import
raises `FileNotFoundError` for the Rome file).

## Evidence

Measure with:

    grep -ro "rome_100ad" sim --include=*.py | grep -v tests | wc -l
    grep -rEoi "denari|roman|\brome\b|iuger" sim/engine sim/world --include=*.py | wc -l

- Engine and tool code names `rome_100ad` directly (defaults, fast paths,
  per-civilisation tables); see also `Complaints/135-engine-names-civilisation-ids.md`.
- Roman units are the engine's units: prices and wages are in denarii,
  land in iugera, and many comments, constants and player texts assume them.
- Tests use Rome as the default fixture, so the suite cannot tell a Rome
  assumption from a general rule.

## What it would take

- A civilisation is data built on one general model (a country with a
  population, territory, institutions, money standard and technologies);
  Rome is one instance. No code path may require a particular instance.
- Units internal to the engine are physical (labour-hours, kilograms,
  hectares); each civilisation's own units (denarius, iugerum) exist only at
  the display edge, from its data file.
- The default civilisation comes from the `default_civ` setting, and the game
  must start with any subset of civilisation files present.
- A test that removes Rome from a temporary copy of the data and starts a game
  with every remaining civilisation.
