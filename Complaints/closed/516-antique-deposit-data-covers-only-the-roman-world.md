# Antique deposit data covers only the Roman world, so other countries have no ore

**Status:** closed

`data/world/geography/deposits/ancient.json` lists the lead, silver, copper and iron deposits worked in antiquity
around the Mediterranean and north-west Europe; `metals.json` lists modern mines. Ore fields worked in antiquity
elsewhere (Chinese, Indian, Iranian, Anatolian beyond the Roman border, and so on) are missing. In a Rome game the
agent economy also runs the other countries; their demand for silver placed lead smelters in China whose nearest
galena in the data was in Gaul, so they never received ore and sat idle (found in 473; the siting fix there now
gives a country with no ore in reach no smelters, which is only right if the data is right).

Measure: list the deposit entries per country or region for each mineral
(`python3 -c` over the two files' `entries`, grouping by `lat`/`lon` into the map's countries; no committed
command yet).

What it would take: deposit entries, with sources, for the ore fields each civilisation in `data/` could work at
its start date, so every country's mines and smelters stand on real ground; and a `validate` warning when a
country has demand for a metal and no deposit of its ore within reach.

## Resolution

- The catalogue already held ore fields for the Chinese, Indian, Iranian, Central Asian, Mesoamerican, African and
  Scandinavian districts (`reference_output_sites.json`, found by measuring rather than by reading this complaint);
  what the shipped civilisations lacked was gold and mercury in China and in Mexico. Added to `ancient.json`, each
  with its source and `conf` D, as known locations of unknown size (`working_unknown`): the Poyang placer gold and
  the Wanshan cinnabar for Han China, the Tlapa placer gold and the Sierra Gorda cinnabar for the Mexica.
- `python3 sim/simulator.py validate` warns of a metal a civilisation demands (its coin, a household need or a
  technique it can run consumes it) that no deposit worked at its start lies within reach of (`sim/engine/validate_ore_reach.py`,
  reach from the `ore_supply_reach_level` map parameter). A civilisation that bought the metal abroad says so in
  `imported_ores` with a reason (Norse tin, gold, mercury; English mercury).
- `sim/tests/test_ore_in_reach.py`: every shipped civilisation has copper, tin, lead and iron in reach or declares
  the import, and `validate` has nothing to warn of.
- Complaint 519: the opening price of every ore over its making cost is unchanged by this data (the new rows are
  unsized, so they name no site), so 519 is not a missing-deposit problem; it stays open. The unsized and
  worked-out rows are filed as 520.
