# Reach and built roads are not read by the engine

**Status:** open

Geography can now route over tiles by any mode a civilisation holds, with roads and railways as built improvements the caller records (`api.route`, `api.reach`, `api.edge_key`; `sim/geography/INTERFACE.md`). Labour reach (Complaint 134), region reach bands (`Geography.region_reach`, calibrated against hand-set `reach_from_italia` figures, Complaints 328 and 378) and the economy's market areas (Complaint 401) still use distances and bands instead.

What it would take: the engine keeps a saved `improvements` map of built roads and track per edge, built by projects that cost labour and material per km by terrain; labour reach becomes `api.reach` within a day budget; region reach and `material_reach` become route cost from the home tiles. `sim/engine/economy_mining.py` also still falls back to the region id "italia" by name.
