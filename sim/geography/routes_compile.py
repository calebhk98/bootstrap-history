"""The search graph for one set of modes, improvements and prices: states are (tile, mode).

Each state's outgoing links carry cost per tonne, days and km. Cost is money per tonne-km from the
caller's `mode_costs` (scaled by how the edge's grade or current changes the carrier's physical
rate against a level, still-water edge) or, when absent, the physical cost of `routes_rates`.
A haul pays a mode's handling each time it changes to that mode, and when it starts.

Improvements are a caller-owned dict {edge_key: {"road": true, "rail": true, "grade": g,
"engineered": true}}. A mode that `needs_improvement` runs only on edges carrying that key; the way
is levelled to the mode's `built_grade_cap` (or the improvement's own `grade`), and an edge steeper
than the mode's `max_natural_grade` needs `engineered`. A land edge that crosses a river (`bridge` in
the improvements) is forded by a land mode at that mode's own handling, crossed only by a bridge by a
mode that is `bridge_only`. A built `port` (keyed by its tile) takes the sea edges of the harbours
bordering it.

Standalone: the route graph, rates and modes of this package.
"""
import json
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

from sim.geography import routes_graph, routes_modes, routes_rates, sea_freight
from sim.geography.map_source import WorldMap

Link = Tuple[int, float, float, float, routes_rates.Rate]  # to_state, cost, days, km, rate


@dataclass
class Compiled:
    tile_ids: Tuple[str, ...]
    tile_index: Dict[str, int]
    mode_ids: Tuple[str, ...]
    links: List[List[Link]]
    modes_at: List[Tuple[int, ...]]
    handling: List[Tuple[float, float]]  # per mode: cost per tonne, days
    trees: Dict[Any, Any] = field(default_factory=dict)


def _handling(mode: Dict[str, Any], mode_id: str, handling_costs: Optional[Mapping[str, float]]) -> Tuple[float, float]:
    if handling_costs is not None:
        cost = handling_costs.get(mode_id, 0.0)
    else:
        default = sea_freight.PORT_HANDLING_HOURS_PER_TONNE if mode.get("model") == "sailing" else 0.0
        cost = mode.get("handling_hours_per_tonne", default)
    return float(cost), float(mode.get("handling_days", 0.0))


def _built_way(mode: Dict[str, Any], edge: routes_graph.Edge, improvement: Dict[str, Any]) -> Optional[float]:
    """The grade of the built way on this edge for the mode, or None when it cannot be built here."""
    if edge.grade > mode.get("max_natural_grade", float("inf")) and not improvement.get("engineered"):
        return None
    return float(improvement.get("grade", min(edge.grade, mode.get("built_grade_cap", edge.grade))))


def _skeleton(world_map: WorldMap, ordered, improvements) -> list:
    """Every link the modes and improvements allow, in compile order, apart from what prices decide:
    (from state, to state, km, rate, physical cost, level ratio, fords, lane nodes), whatever nodes are held.
    Kept on the map."""
    kept = world_map.__dict__.setdefault("_route_skeletons", {})
    key = (ordered, json.dumps(improvements or {}, sort_keys=True))
    found = kept.get(key)
    if found is not None:
        return found
    route_graph = routes_graph.graph(world_map)
    table = routes_rates.rate_table(world_map)
    chosen = routes_modes.modes(world_map)
    tile_index = {tile_id: index for index, tile_id in enumerate(route_graph.tile_ids)}
    count = len(ordered)
    ratios: Dict[Any, Any] = {}
    skeleton = []
    for edge in route_graph.edges + tuple(routes_graph.harbour_edges(world_map, improvements)):
        index_a, index_b = tile_index[edge.tile_a], tile_index[edge.tile_b]
        improvement = (improvements or {}).get(edge.key, {})
        for position, mode_id in enumerate(ordered):
            mode = chosen[mode_id]
            if edge.edge_class not in mode["edge_classes"]:
                continue
            grade, km = edge.grade, edge.km
            needed = mode.get("needs_improvement")
            if needed:
                if not improvement.get(needed):
                    continue
                grade = _built_way(mode, edge, improvement)
                if grade is None:
                    continue
                km *= mode.get("km_factor", 1.0)
            fords = False
            if edge.crosses_river and not improvement.get("bridge"):
                crossing = mode.get("river_crossing", "ford")
                if crossing == "bridge_only":
                    continue
                fords = crossing == "ford"
            for source, target, current in ((index_a, index_b, edge.current_km_per_hour),
                                            (index_b, index_a, -edge.current_km_per_hour)):
                rate = table.rate(mode_id, edge.edge_class, grade, current)
                if rate is None:
                    continue
                physical = routes_rates.physical_cost(world_map, rate)
                level_key = (mode_id, edge.edge_class)
                if level_key not in ratios:
                    level = table.rate(mode_id, edge.edge_class, 0.0, 0.0)
                    ratios[level_key] = routes_rates.physical_cost(world_map, level) if level else 0.0
                level_cost = ratios[level_key]
                skeleton.append((source * count + position, target * count + position, km, rate, physical,
                                 physical / level_cost if level_cost > 0.0 else 1.0, fords, edge.lane_nodes))
    if len(kept) >= 4:
        kept.clear()
    kept[key] = skeleton
    return skeleton


def compile_graph(world_map: WorldMap, mode_ids, improvements, mode_costs, handling_costs,
                  held_nodes: FrozenSet[str]) -> Compiled:
    route_graph = routes_graph.graph(world_map)
    chosen = routes_modes.modes(world_map)
    ordered = tuple(sorted(mode_ids))
    count = len(ordered)
    tile_count = len(route_graph.tile_ids)
    links: List[List[Link]] = [[] for _ in range(tile_count * count)]
    handling = [_handling(chosen[mode_id], mode_id, handling_costs) for mode_id in ordered]
    # per mode: its cost per tonne-km when prices name it (else None: the physical cost stands)
    priced = [None if mode_costs is None or mode_id not in mode_costs else mode_costs[mode_id] for mode_id in ordered]
    for from_state, to_state, km, rate, physical, ratio, fords, lane_nodes in _skeleton(world_map, ordered, improvements):
        if not lane_nodes <= held_nodes:
            continue
        price = priced[from_state % count]
        money = physical if price is None else price * ratio
        ford_cost, ford_days = handling[from_state % count] if fords else (0.0, 0.0)
        links[from_state].append((to_state, km * money + ford_cost, km / rate.km_per_day + ford_days, km, rate))
    modes_at = [tuple(position for position in range(count) if links[tile * count + position])
                for tile in range(tile_count)]
    return Compiled(route_graph.tile_ids, {tile_id: index for index, tile_id in enumerate(route_graph.tile_ids)},
                    ordered, links, modes_at, handling)


def compiled_for(world_map: WorldMap, mode_ids, improvements, mode_costs, handling_costs,
                 held_nodes) -> Compiled:
    """The compiled graph for these inputs, kept on the map's route graph (a few are kept)."""
    held = frozenset(held_nodes or ())
    key = (frozenset(mode_ids), json.dumps(improvements or {}, sort_keys=True),
           json.dumps(mode_costs, sort_keys=True) if mode_costs is not None else None,
           json.dumps(handling_costs, sort_keys=True) if handling_costs is not None else None, held)
    cache = routes_graph.graph(world_map).compiled
    if key not in cache:
        if len(cache) >= 16:
            cache.clear()
        cache[key] = compile_graph(world_map, mode_ids, improvements, mode_costs, handling_costs, held)
    return cache[key]
