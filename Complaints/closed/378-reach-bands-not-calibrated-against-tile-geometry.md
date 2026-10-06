# Reach bands and route difficulty are not calibrated against tile geometry

**Status:** closed - folded into 411

Split from 328. Region anchors now come from tiles, but `Sim.RAW_DISTANCE_BANDS`, `REACH_SPEED_COEF` and each region's `route_difficulty` were tuned against the old hand-set points. Thirteen civilisation-region pairs moved one band when the anchors changed (run the before and after comparison of `Sim.region_reach` over every civilisation).

## What it would take

Re-derive the bands and difficulties from tile geometry (distance between tile-derived centres, coastline and borders from the tiles), then check the fingerprint and the foreign-trade tests. Related: 328, 136.
