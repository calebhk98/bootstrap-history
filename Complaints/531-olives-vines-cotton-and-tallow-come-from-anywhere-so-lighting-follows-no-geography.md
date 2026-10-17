# Olives, vines, cotton and tallow come from anywhere, so lighting follows no geography

**Status:** partly done. Crops carry climates, the lamp takes a vessel, linen-wick and beeswax lights exist (`sim/tests/test_lighting_inputs.py`). Open: `fat_kg` from herds (532), rush wick (no rush entry), a knowledge gate for olives in the Americas, the smoke/softening quality term, and the Mediterranean-versus-northern spending test.

Reference (an outside summary, not code-aware): in antiquity the Mediterranean, the Near East and
North Africa lit rooms with pottery lamps burning olive or castor oil; tallow candles smoked, stank
and melted in heat, beeswax was a luxury, and chandlery became a large trade only in medieval
northern Europe, where olive oil was imported and cattle tallow was plentiful. Under 4.1 that pattern
must fall out of where olives and livestock are, not be written in.

## What the data does

The light need (`data/world/needs.json`) is met by `light_tallow_candle`, `light_oil_lamp` and
`light_electric_lamp` (`data/production/99_lighting.json`), mixed by cost per kilolumen-hour
(`sim/world/need_basket.py`). The inputs behind them carry no geography:

- `olive_oil_kg`, `wine_common_kg` and `cotton_kg` (`data/production/40_organics.json`) have no
  `grown_in_climate_classes` and `requires_node: null`, so they grow on any arable land in every
  civilisation. Only a handful of crops state climates (`grep -c grown_in_climate_classes data/production/*.json`).
- `fat_kg` is a slaughter byproduct with no livestock input: a fixed labour cost per kilogram in
  every civilisation, whatever animals it keeps (Complaint 365 has living stock modelled as research).
- The candle's wick is `wick_cotton_m`, so Rome and England light with cotton; their wicks were
  linen, papyrus pith or rush.
- The lamp vessel (a potter's product) is not an input to `light_oil_lamp`, and there is no beeswax
  candle although `wax_kg` exists.
- Light is valued in lumen-hours only; tallow's smoke, smell and softening in heat do not enter.

## Evidence

    for c in rome_100ad england_1300 norse_900ad mexica_1500; do python3 -c "from sim.tests.harness import sim; s=sim(civ='$c'); print('$c', {g: round(s._material_price_per_kg(g),4) for g in ('light_tallow_candle','light_oil_lamp','olive_oil_kg','tallow_kg')})"; done

- Rome: the candle is slightly cheaper per kilolumen-hour than the lamp, so the mix spends a little
  more on candles than on lamps (the share ratio of two goods does not depend on the others in the mix).
- England 1300 and Norse 900: olive oil is cheaper than tallow and the lamp beats the candle, the
  reverse of the record.
- Mexica 1500: olive oil is priced and the lamp beats the candle, with no olive trees and no
  cattle or sheep in the Americas.

## What it would take

- Climate classes on `olive_oil_kg`, `wine_common_kg` and `cotton_kg` (and a sweep of the other
  extracted crops), so they are bought from a partner where they do not grow (`sim/engine/crop_climate.py`).
- `fat_kg` drawn from living stock, so tallow follows herds.
- A wick from the society's own fibre (flax, papyrus, rush), the lamp vessel as an input, and a
  beeswax candle from `wax_kg`.
- Optionally a quality term (smoke, heat softening) on tallow, labelled as a heuristic until a
  mechanism for indoor air exists.
- A test: with climates set, a Mediterranean start spends more on oil lamps than candles and a
  northern one the reverse, measured, not asserted from a rule naming either civilisation (4.7).

## Done

- `olive_oil_kg`, `wine_common_kg`, `cotton_kg` carry `grown_in_climate_classes`; England and Norse no longer solve olive oil or cotton (`python3 -m sim.tests --only lighting_inputs`). Mexica holds olive-suitable tiles, so it still makes olive oil: a climate list cannot say the Americas did not know the tree; that is a knowledge gate (`requires_node`).
- `wick_linen_m` (from `linen_kg`, an overcount since that entry includes weaving), `light_tallow_candle_linen_wick`, `light_oil_lamp_linen_wick`, `light_beeswax_candle` (from `wax_kg`); `light_oil_lamp` takes `ceramic_kg` as its vessel.
