# Tile fertility and region fertility are two scales that disagree

**Status:** open

`data/world/geography.json` carries `fertility_quality_multiplier` on each region
(1.0 defined as Italia, the wheat yield reference) and on each `land_tiles` tile
(generated from a Koppen-Geiger mix, not anchored to Italia). The arable-weighted
mean of a region's tiles differs from its region value, and for the reference
region the tile mean is below 1.0. Farm land quality now reads tiles
(Complaints/52), so Rome's farm sits on soil rated worse than the yield model's
"decent land" reference, which lowers every civilisation's food and weakens the
baseline.

Compare with: a short script over `land_tiles.region_to_tiles` against
`regions.<id>.land.fertility_quality_multiplier` (throwaway, not committed).

The two need one scale. Either rescale tiles so the Italia tile mean is the
reference, or drop the region-level value and define the reference from the tiles.
Do not tune either to a target population.
