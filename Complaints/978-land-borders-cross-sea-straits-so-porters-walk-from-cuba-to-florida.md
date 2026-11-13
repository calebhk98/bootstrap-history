# Land borders cross sea straits, so porters walk from Cuba to Florida

**Status:** open - generator and data fixed on branch `land-borders-not-across-straits`; awaiting a whole-game check before closing

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

**What changed.** `tools/generate_geography_tiles.py` rule 8 now keeps a grid-adjacent pair as a land border only where `land_touches` holds:
each cell's clipped land has landmasses within `LAND_TOUCH_TOLERANCE_METRES` of the other cell's land, and those landmasses hold at least
`LAND_TOUCH_MINIMUM_SHARE` of that cell's land (a labelled threshold: the plain "land polygons touch" test still joined `cuba_03` to
`united_states_of_america_02` through the Florida Keys, a sliver of the Cuban cell's land). `coastal` is unchanged (it never read `borders`),
so sea access works as before. `tile_grid.json` was regenerated; only the `borders` lists and the rule-summary text changed (the tiles'
`source` prose in the generator is newer than the committed file and was left as committed). `cuba_03` no longer borders the mainland by
land, and the France-Spain tiles still do. Tests: `LandTouchesTests` and the island-border and real-border checks in
`sim/tests/test_geography_tiles.py`. Count removed pairs with a diff of `borders` against `origin/complaints-cleanup`.

**Review of the removed pairs.** Each removed pair was classified from the Natural Earth clip (compare `borders` against `origin/complaints-cleanup`):
no land within the tolerance of the shared edge (grid adjacency only, so the land meets, if at all, at a corner through another tile, and
the pair stays joined in the land graph by a short detour through the other two cells of the square), or land touches only through a
minor piece of one cell (a sliver of the tile's land). The flagged pairs: `norway_05` is Svalbard, `finland_01` meets Sweden across the
Gulf of Bothnia (the Torne pair `finland_02`-`sweden_05` stays), `north_korea_01`-`south_korea_03` has no land near the shared edge
(Korea stays joined through `china_58`-`south_korea_02`), `india_08`-`india_09` meets only through a sliver (`india_08` keeps `india_13`).
Known limit: a tile that holds a minor piece of another landmass above the share (for example `algeria_15`-`spain_02`,
`cuba_02`-`dominican_rep_01`) still gets a land border; that needs per-landmass nodes, not a different threshold. The share is declared
`temporary_heuristic` `LAND_TOUCH_MINIMUM_SHARE` in the generator with `retire="Complaints/978"`.

## Cut-off islands drop out of the carriage table (found tracing Norse, 2026-11-11)

The Svalbard tiles (`norway_04` to `norway_06`) are Norse home tiles with people but lost their only land links. `CarriageTable.costs_from`
now omits them entirely, although `data/world/geography/sea_links/links.json` lists sea links for them, so an island cut off by land
does not trade by sea. A processor's output haul now averages only over the areas a tile reaches (`location_inputs.output_haul_cost`),
so the unreachable area no longer stops every placement; `mean_haul_cost` for inputs has the same shape and is not yet changed. Open:
an island tile with sea links is reached by the sea modes in the carriage table.
