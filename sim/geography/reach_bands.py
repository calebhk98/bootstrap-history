"""How far each region is from the tiles a party holds, as a reach level.

A region is a label over tiles. Its reach is the fewest days of travel from any held tile to any of
its tiles over the modes the party can use (and the ways it has built), banded on a geometric ladder:
level 0 is a region the party holds a tile of, and a region no route joins is the farthest level.
The ladder comes from the carriers' own days per tile (`ladder`): the first step is the days the slowest
carrier that works the coast takes over a typical coastal edge, and each later step multiplies by the
fastest carrier's pace over the slowest's, spread over the steps the levels leave.

Standalone: the route search and tile holdings of this package.
"""
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from sim.geography import routes_graph, routes_modes, routes_rates, routes_search, tile_holdings
from sim.geography.map_source import WorldMap

UNBOUNDED_DAYS = 1.0e9


def farthest_level(world_map: WorldMap) -> int:
    """The highest reach level the map's `reach_levels` define."""
    return max(int(level_id) for level_id in world_map.catalogue("reach_levels"))


def _level_paces(world_map: WorldMap) -> Dict[str, Dict[str, float]]:
    """{mode id: {edge class: km a day on level, still ground or water}} for the modes that have a rate."""
    paces: Dict[str, Dict[str, float]] = {}
    for mode_id, mode in routes_modes.modes(world_map).items():
        for edge_class in mode["edge_classes"]:
            rate = routes_rates.compute_rate(world_map, mode, edge_class, 0.0, 0.0)
            if rate is not None:
                paces.setdefault(mode_id, {})[edge_class] = rate.km_per_day
    return paces


def _hop_days(world_map: WorldMap, paces: Dict[str, Dict[str, float]], edge_class: str) -> Optional[float]:
    """Days the slowest carrier that works `edge_class` takes over that class's mean edge, or None when the
    map has no such edge or no carrier works it."""
    kilometres = [edge.km for edge in routes_graph.graph(world_map).edges if edge.edge_class == edge_class]
    carriers = [by_class[edge_class] for by_class in paces.values() if edge_class in by_class]
    if not kilometres or not carriers:
        return None
    return sum(kilometres) / len(kilometres) / min(carriers)


def ladder(world_map: WorldMap) -> Tuple[float, float]:
    """(first_days, ratio) of the reach bands, derived from the carriers: the first step is a coastal hop
    at the slowest coastal carrier's pace (a land hop at the slowest land carrier's when the map has no
    coast edges), and the ratio is the fastest carrier's pace over the slowest's, spread over the steps
    between the first band and the farthest. Kept on the map."""
    cached = world_map.__dict__.get("_reach_ladder")
    if cached is None:
        paces = _level_paces(world_map)
        every = [pace for by_class in paces.values() for pace in by_class.values()]
        first = next((hop for hop in (_hop_days(world_map, paces, edge_class) for edge_class in ("coast", "land"))
                      if hop is not None), None)
        steps = max(1, farthest_level(world_map) - 2)
        cached = (0.0, 1.0) if first is None or not every else (first, (max(every) / min(every)) ** (1.0 / steps))
        world_map.__dict__["_reach_ladder"] = cached
    return cached


def level_of(world_map: WorldMap, days: Optional[float]) -> int:
    """The reach level of a place `days` away (None when no route joins it), 0 only for days of zero."""
    top = farthest_level(world_map)
    if days is None:
        return top
    if days <= 0.0:
        return 0
    edge, ratio = ladder(world_map)
    for level in range(1, top):
        if days <= edge:
            return level
        edge *= ratio
    return top


def _days_from(world_map: WorldMap, held_tiles: Iterable[str], held_nodes: Iterable[str],
               improvements: Optional[Mapping[str, Mapping[str, Any]]]) -> Dict[str, float]:
    """{tile: fewest days from any held tile} over the modes the held nodes open; empty when nothing is held."""
    held_tiles = list(held_tiles)
    if not held_tiles:
        return {}
    nodes = frozenset(held_nodes)
    modes = routes_modes.usable_modes(world_map, [nodes])
    return routes_search.reach(world_map, held_tiles, modes, UNBOUNDED_DAYS, improvements, held_nodes=nodes)


def tile_levels(world_map: WorldMap, held_tiles: Iterable[str], held_nodes: Iterable[str],
                improvements: Optional[Mapping[str, Mapping[str, Any]]] = None) -> Dict[str, int]:
    """{tile: reach level} for every tile of the map, from the tiles held: 0 for a held tile, the farthest
    level for a tile no route joins."""
    days = _days_from(world_map, held_tiles, held_nodes, improvements)
    return {tile_id: level_of(world_map, days.get(tile_id)) for tile_id in world_map.tiles}


def region_levels(world_map: WorldMap, held_tiles: Iterable[str], held_nodes: Iterable[str],
                  improvements: Optional[Mapping[str, Mapping[str, Any]]] = None) -> Dict[str, int]:
    """{region id: reach level}: the nearest level among the region's tiles."""
    days = _days_from(world_map, held_tiles, held_nodes, improvements)
    levels = {}
    for region_id in sorted(tile_holdings.region_ids(world_map)):
        reached = [days[tile] for tile in tile_holdings.tiles_of_regions([region_id], world_map) if tile in days]
        levels[region_id] = level_of(world_map, min(reached, default=None))
    return levels
