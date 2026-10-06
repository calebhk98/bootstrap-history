# The economy keeps its own tile freight graph

**Status:** closed - pinned by sim/tests/test_economy_tile_costs.py (`GeographyIsTheSourceTests`): the economy's carriage costs equal geography's route costs, and a river link on the map is cheaper by boat in the economy

`sim/economy/tile_costs.py` builds a freight graph over the land tiles (border links, sea links between coastal tiles within a range, detour factors) and runs its own shortest-path search, because geography had no tile graph. Geography now has one (`sim/geography/routes_graph.py`, `routes_search.py`, reached through `sim/geography/api.py`) with the same edge meaning plus rivers, terrain, walking without roads, built roads and rail, and per-mode cost. Two graphs of the same tiles drift apart: a river or road added to geography's map does not reach market areas.

Evidence: compare `tile_costs.build_edges` with geography's `links()` output (`python3 -c "from sim.geography import api; ..."`, see `sim/geography/INTERFACE.md`).

What it would take: `tile_costs` takes its links from the geography api (its `extra_links` hook already accepts them), then deletes its own edge builder and search. The economy package belongs to another owner, so this was not changed from the geography branch.

**Resolution.** `tile_costs.CarriageTable` asks `sim.geography.api.route_costs` (new; one search per source tile, cached on the map's compiled graph) with the economy's money per tonne-km by geography mode id (`cart`, `pack`, `river_boat`, `sail`). The economy's own edge builder, search, detour and range constants and the unused rate function are deleted; the setup carries the held tech nodes (sea lanes) and an optional map (`api.map_of_tiles` for scenarios that place their own tiles). The economy's own haversine is deleted; `sim/geography/distance.py` holds the great-circle distance (the chordal position in `sim/engine/core.py` is a different measure, kept on purpose).
