# Reach and built roads are not read by the engine

**Status:** open

Geography can now route over tiles by any mode a civilisation holds, with roads and railways as built improvements the caller records (`api.route`, `api.reach`, `api.edge_key`; `sim/geography/INTERFACE.md`). Labour reach (Complaint 134), region reach bands (`Geography.region_reach`, calibrated against hand-set `reach_from_italia` figures, Complaints 328 and 378) still use distances and bands instead (the economy's market areas now read geography's route costs, Complaint 408).

What it would take: the engine keeps a saved `improvements` map of built roads and track per edge, built by projects that cost labour and material per km by terrain; labour reach becomes `api.reach` within a day budget; region reach and `material_reach` become route cost from the home tiles. `sim/engine/economy_mining.py` also still falls back to the region id "italia" by name.

Labour reach now reads `api.reach` over the modes held (Complaint 134, closed). It passes no
`improvements`, since the engine keeps none yet. Relocating the household's base still uses a straight-line
walking pace (`labour_settlement.relocation_quote`). `api.route` from spain_03 to algeria_01 returns
5,357 km and 228 days for rome_100ad, about three times the straight-line quote, which reads as a
cheapest-freight path rather than the fastest way a household would travel. A fastest-route query, or a
route weighted by days, would let relocation use geography too.


## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 414 (`closed/414-food-potential-is-not-read-by-demography-or-settlement.md`): food potential is not read by demography or settlement (settlement still uses arable times fertility).
- 415 (`closed/415-mining-does-not-read-endowment-or-prospecting.md`): mining does not read endowment or prospecting; a mine should name a found deposit.
- 440 (`closed/440-the-port-does-not-hand-the-economy-site-limits-or-read-its-extraction.md`): the port does not hand the economy site limits or read its extraction.
- 138 (`closed/138-barren-land-has-no-food-but-farming.md`): barren land has no food but farming: the remaining piece is 414 (above).
- 281 (`closed/281-deposit-tile-is-a-coarse-hand-assignment.md`): deposit tile is a coarse hand assignment; surveyed positions per mine (owner: later).
