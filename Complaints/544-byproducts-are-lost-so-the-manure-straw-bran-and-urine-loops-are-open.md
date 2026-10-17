# Byproducts are lost, so the manure, straw, bran and urine loops are open

**Status:** open

Reference (an outside summary of an ancient input-output table, not code-aware): straw from the
fields and bran from the mill fed the draught and pack animals; their manure went back to the
fields; town urine and nightsoil were collected for fullers, tanners and gardens. Linking these is
what keeps mass from being wasted and ties town to country.

## What the data does

- **No straw or bran.** Milling loses its 4% as "moisture and dust" (`data/production/95_grain_milling.json`);
  grain recipes output grain only. Nothing feeds animals from the harvest (draught animals take no
  inputs at all, 532).
- **Manure is extracted, not excreted.** `manure_kg` (`data/production/40_organics.json`) is a
  standalone recipe with no animals behind it, and its only consumer is saltpetre (`nitre_kg`,
  `60_nitrogen.json`). Farms do not take it; soil has no nutrient stock for it to restore (543).
- **No urine or nightsoil.** No recipe collects them, and fulling and tanning do not ask for them (533).
  Town waste goes only to the disposal sink (`99_waste_disposal.json`), which is a cost.

A static graph check of `data/production/`: every input has a recipe that makes it (no orphan
inputs). Outputs that nothing consumes are harder to list statically because tree nodes and state
lines also consume goods; 533 asks for that check in `simulator.py validate`.

## What it would take

- Joint outputs: straw with grain, bran with flour, manure with herds and draught animals (532),
  urine and nightsoil with town population.
- Consumers: fodder from straw and bran for animals, manure for soil nitrogen (543), urine for
  fulling and tanning, nightsoil for market gardens; disposal only for what nobody buys.
- Prices of these byproducts then fall out of the joint production, and a town's waste becomes worth
  carting when the fields need it.
