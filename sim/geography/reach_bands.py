"""How far each region is from the tiles a party holds, as a reach level.

A region is a label over tiles. Its reach is the fewest days of travel from any held tile to any of
its tiles over the modes the party can use (and the ways it has built), banded on a doubling ladder:
level 0 is a region the party holds a tile of, and a region no route joins is the farthest level.
The first step and the ratio are map parameters (`reach_band_first_days`, `reach_band_ratio`).

Standalone: the route search and tile holdings of this package.
"""
from typing import Any, Dict, Iterable, Mapping, Optional

from sim.geography import parameters, routes_modes, routes_search, tile_holdings
from sim.geography.map_source import WorldMap

UNBOUNDED_DAYS = 1.0e9


def farthest_level(world_map: WorldMap) -> int:
    """The highest reach level the map's `reach_levels` define."""
    return max(int(level_id) for level_id in world_map.catalogue("reach_levels"))


def level_of(world_map: WorldMap, days: Optional[float]) -> int:
    """The reach level of a place `days` away (None when no route joins it), 0 only for days of zero."""
    top = farthest_level(world_map)
    if days is None:
        return top
    if days <= 0.0:
        return 0
    edge = float(parameters.parameter(world_map, "reach_band_first_days"))
    ratio = float(parameters.parameter(world_map, "reach_band_ratio"))
    for level in range(1, top):
        if days <= edge:
            return level
        edge *= ratio
    return top


def region_levels(world_map: WorldMap, held_tiles: Iterable[str], held_nodes: Iterable[str],
                  improvements: Optional[Mapping[str, Mapping[str, Any]]] = None) -> Dict[str, int]:
    """{region id: reach level} from the tiles held, over the modes the held nodes open."""
    held_tiles = list(held_tiles)
    nodes = frozenset(held_nodes)
    days: Dict[str, float] = {}
    if held_tiles:
        modes = routes_modes.usable_modes(world_map, [nodes])
        days = routes_search.reach(world_map, held_tiles, modes, UNBOUNDED_DAYS, improvements, held_nodes=nodes)
    levels = {}
    for region_id in sorted(tile_holdings.region_ids(world_map)):
        reached = [days[tile] for tile in tile_holdings.tiles_of_regions([region_id], world_map) if tile in days]
        levels[region_id] = level_of(world_map, min(reached, default=None))
    return levels
