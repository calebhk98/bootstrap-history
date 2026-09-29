# The game assumes Rome exists

**Status:** open

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
