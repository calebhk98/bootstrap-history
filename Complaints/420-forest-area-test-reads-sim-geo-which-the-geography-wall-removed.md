# The forest-area test reads `Sim.geo`, which the geography wall removed

**Status:** open

`python3 -m sim.tests --only complaint_45_forest_area_not_region_count` crashes:
`AttributeError: 'Sim' object has no attribute 'geo'`. The test reads
`sim_under_test.geo["land_tiles"]` (lines 29-30 of the test file). The geography wall made geography
reachable only through `sim.geography` and `sim/geography/api.py`. It fails the same way on main
(`bcd8b65`).

Why it matters: the regression test for Complaint 45 (forest area by tiles, not by region count) protects
nothing while it crashes.

What it would take: read the tiles through the geography surface, adding a member to `api.py` if none
gives the land-tile table.
