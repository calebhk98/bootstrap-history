# Disease is one national patch with a dice-roll importation

**Status:** partly - every civilisation runs the pathogen model with contact-driven arrival and no dated plagues (test: `plagues_from_contact`); spatial patches and trade-scaled contact remain

- `sim/engine/disease_port.py` steps one patch ("The nation is one patch"); only the deaths are spread over
  603's tiles. There is no per-region disease load, so campaign and settlement cost cannot depend on where.
- A pathogen arrives by a yearly chance (`DISEASE_TRAVELLER_ANNUAL_CHANCE`, labelled temporary heuristic in
  `sim/disease/nation_tuning.py`) that falls with route days to the tiles held. It does not travel along trade
  or route edges scaled by density and volume.
- `sim/world/military_logistics.py` has no disease term; colonies take the national burden.
- No initial immunity for civilisations whose childhood diseases are already endemic (England 1300).
- The outside world is not simulated actors; named outside sources are data (`disease_exposure.outside_contact`).

Why it matters: the group wants plagues to spread along busy connections and armies to suffer in
disease-heavy regions. CLAUDE.md 4.2: a baseline that reliably reproduces a dated plague is evidence of cheating;
the dated plague hazards are already deleted from every start (`grep -n -i plague data/civilizations/*.json`
finds only foreknowledge text and notes).

What it would take: the "spatial stage" `disease_port.py` and `data/disease/_SCHEMA.md` already name: one patch
per region (603), exchange along route edges by travel volume, and contact scaled by trade volume and density.
