# Land borders cross sea straits, so porters walk from Cuba to Florida

**Status:** open - found tracing Complaint 613; not fixed

**What is wrong.** A tile's `borders` (`data/world/geography/tile_grid.json`) are grid edge-adjacency (`tools/generate_geography_tiles.py`,
rule 8): two cells that each hold some land and share a grid edge border each other even when the water between them is a strait.
`sim/geography/routes_graph.py` `_land_and_river_edges` makes a `land` edge for every pair in a tile's `borders`, and the foot mode
(`data/world/geography/route_modes/modes.json`, `edge_classes: ["land"]`) walks any land edge. So `cuba_03` borders
`united_states_of_america_02` across the Florida Strait, and a porter route from `cuba_01` to `mexico_12` walks through Florida and the
United States tiles (a breadth-first walk of `borders` gives cuba_01, cuba_04, cuba_03, united_states_of_america_02, the US tiles,
mexico_13, mexico_12). Mexica merchants then plan foot hauls of hundreds of days from the islands, which is part of the porter demand in 613.

**Why it matters.** Islands are reachable on foot, so a society without ships trades with them as if by land (4.3: geography should
bind through normal rules), and carriage hours and costs on such routes are wrong.

**What it would take.** A land border only where the two tiles' land touches across their shared edge: the generator checks the
Natural Earth land along the shared edge (or that the two cells' land polygons intersect), and pairs that touch only across water become
sea neighbours, reached by the sea modes. Test: a rule test on two built cells with water between them gives no land border; a data
test that `cuba_03` does not border a mainland tile by land.
