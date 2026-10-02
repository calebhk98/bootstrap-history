"""What a state holds on the map: its frontier, its coast and the roads between its tiles.

Read from the equal-area tiles in `data/world/geography.json` and a civilisation's
`home_regions`. Nothing here is specific to a civilisation; a state that holds other
tiles holds other lengths.

[temporary_heuristic] A shared edge between two tiles is one tile's width long, and a
road runs along every edge between two tiles the state holds (the tile centres are one
tile width apart). A coastal tile has one tile width of coast. Real coastlines and road
networks are not grids; the lengths are of the right order and move with what is held.
"""
import functools
import math
from typing import Dict, List, NamedTuple, Tuple

from sim.world import land


class Holdings(NamedTuple):
	tile_count: int
	frontier_km: float  # land border with tiles the state does not hold
	coast_km: float
	road_km: float  # links between neighbouring held tiles


@functools.lru_cache(maxsize=64)
def _tiles() -> Tuple[Dict[str, dict], float]:
	geography = land._load_json(land.GEOGRAPHY_FILE)
	tiles = geography.get("land_tiles", {})
	return tiles.get("tiles", {}), math.sqrt(float(tiles.get("target_tile_area_km2", 0.0)))


@functools.lru_cache(maxsize=64)
def _holdings(home_regions: Tuple[str, ...]) -> Holdings:
	geography = land._load_json(land.GEOGRAPHY_FILE)
	tiles, edge_km = _tiles()
	held = set(land._tile_ids_for_home_regions(list(home_regions), geography.get("land_tiles", {})))
	frontier = sum(1 for tile_id in held for neighbour in tiles[tile_id]["borders"] if neighbour not in held)
	links = sum(1 for tile_id in held for neighbour in tiles[tile_id]["borders"] if neighbour in held) / 2.0
	coast = sum(1 for tile_id in held if tiles[tile_id].get("coastal"))
	return Holdings(len(held), frontier * edge_km, coast * edge_km, links * edge_km)


def holdings(home_regions: List[str]) -> Holdings:
	"""Frontier, coast and internal road length of the tiles these regions resolve to."""
	return _holdings(tuple(home_regions))
