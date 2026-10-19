# No endemic disease geography, so the tropics keep draught animals and carry no malaria burden

**Status:** closed - endemic disease layers (trypanosomiasis, malaria) derived from tile climate and cover; herd loss and human excess mortality read by the ordinary rules

Reference (an outside design note, not code-aware): sub-Saharan Africa was thinly peopled in
antiquity largely because the tsetse belt (trypanosomiasis) killed horses and oxen, ruling out plough
farming and wheeled carriage, and because malaria raised mortality.

## What the code does

- `data/disease/` holds four epidemic diseases as dated events (Complaint 490). No disease is endemic
  to a place.
- Herd suitability is a climate and terrain envelope (`sim/geography/food_pasture.py`); nothing keeps
  cattle or horses out of a vector belt. Malaria appears only as text in
  `data/world/geography/located_materials/located_materials.json`.

## What it would take

- Endemic diseases as map layers with a host (people, cattle, horses) and an effect: mortality for
  people, herd loss for animals, so draught power, ploughs and carts become unavailable where the
  vector is.
- The effect falls out of the ordinary rules (no plough team, no carts), not a rule naming Africa (4.7).
- Related: 490 (dated plagues), 537 (hoe tier for societies without draught animals).

## Resolution

- `data/disease/endemic/` holds one file per endemic disease: a range, a climate and vegetation envelope (the
  suitability rules of `sim/geography/content_rules.py`), and per host an annual loss at full pressure, each field
  sourced and confidence-tagged (`sim/geography/endemic.py` reads them; `validate` checks them).
- Trypanosomiasis hosts are cattle and horses. Herd food (`food_pasture.herd_contributions`) drops a herd whose loss
  swallows its surplus offtake. Held stock whose row lists `species` (`data/world/living_stock.json`, draught animals)
  loses the place's endemic share on top of its base loss, and the opening herd is cut to what breeding can keep, so
  no draught team exists in the belt and plough recipes have nothing to hold.
- Malaria's host is people: `Population.step(endemic_death_rates=...)` adds the excess death rate per band, scaled by
  the disease burden not yet removed; the engine passes the mean over the held tiles.
- The vector's biogeographic range is data (a box on tile latitude and longitude); nothing in code names a region.
- Tests: `sim/tests/test_endemic_disease.py`. Per-year cost: `python3 -m sim.tests --only endemic_disease`, and the
  query over a civilisation's held tiles takes a fraction of a millisecond.
- Not modelled: trypanotolerant breeds, drugs, fly clearing (a later node effect could lower the pressure).
