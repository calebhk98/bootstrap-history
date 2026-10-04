# Mining does not read endowment or prospecting

**Status:** open

Geography now knows where deposits are and how big (`api.known_deposits`, a catalogue of major mines and oil, gas and coal fields in `data/world/geography/deposits/`), what each tile is expected to hold undiscovered (`api.endowment`), and what prospecting effort finds (`api.prospect`, deterministic from a seed). The mining model still uses a national ceiling scaled by region mineral shares (`sim/engine/economy_mining.py`, `sim/geography/geography.py` `mineral_scale`, `sim/world/mineral_shares.py`), so a player can open any mine of any size anywhere it holds land, and mines never close (Complaint 374).

What it would take: opening a mine names a found deposit (from `prospect` or the catalogue) and draws on its quantity; the engine saves which deposits each actor has found and how much each has yielded (geography saves nothing); the seed comes from saved engine state. Then the region mineral tables in `data/world/geography.json` and `mineral_shares.py` can go, which also removes the last import of `sim.world` from geography (`sim/tests/test_geography_walls.py` allowlist). Related: 281, 334, 374.
