# Deposit model charges no dead work, timbering, ventilation or sorting

**Status:** closed - barren rock, timbering, ventilation, hauling and drainage are charged (348); grade values and processing hours are 641

`ore_grade_kg_per_tonne` in `data/world/deposits.json` is metal per tonne of rock raised, and `sim/world/deposits.py` charges only breaking, a depth multiplier, fire-setting wood and amortised shafts. Not charged, each needing a source before a number moves:

- Barren rock broken between mineralised pods, in drives and in shaft sinking. Bettenay 2022 (Metalla 26.2) says much of the rock raised at Melle was barren and that only about 5-10 percent galena ore was mined. Lead grades in the file (up to 180 kg per tonne, richer than that) read like hand-sorted ore, not run-of-mine; the grade basis needs a source per deposit.
- Timber to hold workings, lighting and ventilation (Agricola book VI; Pliny NH 33.71 for Spain). Bettenay names timbering as a use of wood but gives no quantity.
- Underground sorting and cobbing labour per tonne (the galena recipe carries 5 h per tonne; the silver ore recipe none).
- Shallow medium-rock veins (lead, copper, iron, mercury) charge 12 h per tonne of rock, about 670 kg per eight-hour shift, above Bettenay's all-in 25-250 kg at Melle and above the 385 kg face-only Kongsberg figure for hard rock. The rock is easier, so this may be fine, but no source supports it. Laurion (deep, medium) is 286 kg per shift, slightly above the Melle band.
- The galena, copper ore and iron ore recipes carry their own labour (about 25, 18 and 14 hours per tonne) beside the deposit supply curve; rent only adds the excess over the recipe. Iron, silver ore and coal get no rent from the curve.

Source not opened: Agricola, De re metallica (no text was reached); Strabo, Pliny, Hopper on Laurion and Davies on Roman mines were also not opened. Only Bettenay 2022 (Metalla 26.2, open-access PDF) was read.
