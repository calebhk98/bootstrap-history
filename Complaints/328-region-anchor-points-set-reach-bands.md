# Region reach and freight read a hand-set anchor point, not tiles

**Status:** partly - anchors are now derived from tiles (pinned by sim/tests/test_region_anchor_from_tiles.py); recalibrating the reach bands is 376

`data/world/geography.json` keeps a `lat`/`lon` per region. `Sim._compute_home_centroid`, `region_reach` and freight distance use it. Replacing it with the area-weighted centre of the region's tiles moves the reach band for some civilisation and region pairs (measured by recomputing `Sim.region_reach` for every civilisation with the anchor swapped; thirteen pairs across the six shipped civilisations changed by one band, e.g. Norse reach to Italia from 1 to 2).

## Why it matters

The anchor is a second source of position next to the tiles, and it is why `Sim._regions` cannot be a pure view over tiles. Swapping it silently changes trade reach.

## What it would take

Derive the anchor from tiles and re-derive `RAW_DISTANCE_BANDS` and `route_difficulty` so reach is calibrated against tile geometry, then check the fingerprint and the foreign-trade tests. Related: 136.

Related: 281.

Owner decision (2026-10-02): should not have been possible; reach and freight must come from tiles.

Done: no region record in `data/world/geography.json` carries lat/lon; `sim/world/regions.py` computes each anchor as the land-area-weighted centre of the region's tiles. Measured by recomputing `Sim.region_reach` for every civilisation before and after: thirteen civilisation-region pairs moved one band, as predicted. Remaining: 376.
