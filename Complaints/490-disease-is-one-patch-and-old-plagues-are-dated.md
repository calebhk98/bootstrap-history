# Disease is one national patch with a dice-roll importation, and older starts still schedule plagues by date

**Status:** open

- `sim/engine/disease_port.py` steps one patch ("The nation is one patch"). There is no per-region disease
  load, so campaign and settlement cost cannot depend on where.
- A pathogen arrives by a yearly chance, `DISEASE_CONTACT_ANNUAL_CHANCE` (labelled temporary heuristic),
  inside a dated contact window. It does not travel along trade or route edges scaled by density and
  volume.
- Only `data/civilizations/mexica_1500.json` uses the pathogen model through `disease_exposure`. Rome
  still carries a dated `Antonine plague` hazard (`data/civilizations/rome_100ad.json`) gated on
  population, and other starts carry dated hazards the same way (`grep -n '"years"' data/civilizations/*.json`).
  CLAUDE.md 4.2 calls a baseline that reliably reproduces a dated plague "evidence of cheating".
- `sim/world/military_logistics.py` has no disease term; colonies take the national burden.

Why it matters: the group wants plagues to spread along busy connections (the Antonine and later
plagues) and armies to suffer in disease-heavy regions.

What it would take: the "spatial stage" `disease_port.py` and `data/disease/_SCHEMA.md` already name:
one patch per region (489), exchange along route edges by travel volume, then retire the dated plague
hazards in favour of pathogens with contact-driven arrival.
