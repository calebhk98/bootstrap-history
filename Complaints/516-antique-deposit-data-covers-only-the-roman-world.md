# Antique deposit data covers only the Roman world, so other countries have no ore

**Status:** open

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
