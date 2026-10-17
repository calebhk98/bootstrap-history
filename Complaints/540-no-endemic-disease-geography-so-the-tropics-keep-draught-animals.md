# No endemic disease geography, so the tropics keep draught animals and carry no malaria burden

**Status:** open

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
