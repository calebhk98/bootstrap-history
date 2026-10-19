# Byproducts are lost, so the manure, straw, bran and urine loops are open

**Status:** closed - straw, bran, dung, urine and nightsoil are made, fed and tipped through ordinary recipes; soil restoration waits on 543

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

## Resolution

- Straw is a joint output of every grain recipe (`wheat_kg`, `wheat_hoe_kg`, `millet_kg`, `maize_kg`).
- Milling now sifts: each flour recipe makes flour and bran together, and keeps a small dust loss.
- Herds (sheep, goat, cattle) and the draught-animal rearing recipe make dung together with their other
  products and eat a winter ration of straw and bran. The per-head factors are fields of the species rows
  in `data/world/living_stock.json`; a test recomputes each recipe from them. The standalone
  dung-extraction recipe is deleted. The nitre bed is the dung consumer.
- Urine and nightsoil: no recipe lets a household output a good, so `data/production/95_town_excreta_and_gardens.json`
  collects them, stating the kilograms excreted per person-year on each. Urine is bought by fulling
  (`cloth_kg`) and tanning (`leather_kg`); nightsoil by a new market-garden recipe (`vegetable_kg`, a food).
- Straw, bran, dung, urine and nightsoil each have a heap in `data/world/waste_heaps.json`, so what
  nobody buys is tipped, and as recorded wastes they carry no share of the cost of the grain, flour or
  herd product that came with them.
- Regression test: `sim/tests/test_byproduct_loops.py` (each joint output exists with its ratio, each has a
  maker and a consumer or heap).
- Not done, and not what this complaint asks: the farm has no yield response to dung or nightsoil (543
  owns the soil nitrogen stock), and the supply of urine and nightsoil is limited only by collection labour
  until households can output goods.
