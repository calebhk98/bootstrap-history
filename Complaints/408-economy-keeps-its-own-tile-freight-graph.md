# The economy keeps its own tile freight graph

**Status:** open

`sim/economy/tile_costs.py` builds a freight graph over the land tiles (border links, sea links between coastal tiles within a range, detour factors) and runs its own shortest-path search, because geography had no tile graph. Geography now has one (`sim/geography/routes_graph.py`, `routes_search.py`, reached through `sim/geography/api.py`) with the same edge meaning plus rivers, terrain, walking without roads, built roads and rail, and per-mode cost. Two graphs of the same tiles drift apart: a river or road added to geography's map does not reach market areas.

Evidence: compare `tile_costs.build_edges` with geography's `links()` output (`python3 -c "from sim.geography import api; ..."`, see `sim/geography/INTERFACE.md`).

What it would take: `tile_costs` takes its links from the geography api (its `extra_links` hook already accepts them), then deletes its own edge builder and search. The economy package belongs to another owner, so this was not changed from the geography branch.
