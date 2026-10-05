"""Cheapest and fastest hauls between tiles over the (tile, mode) graph.

`route` returns the least-cost haul from any origin tile to any destination tile; `reach` the days
to every tile within a budget. A single-source tree is kept per (origin set, graph inputs, metric),
so many destinations from one origin cost one search. Plain data out.

Standalone: the route graph, compile and rates modules of this package.
"""
import heapq
from typing import Any, Dict, Iterable, Mapping, Optional

from sim.geography import routes_compile, routes_modes, routes_rates, routes_graph
from sim.geography.map_source import WorldMap

INFINITY = float("inf")


def _origin_indexes(world_map: WorldMap, tiles: Iterable[str]) -> frozenset:
    chosen = frozenset(tiles)
    unknown = sorted(chosen - set(world_map.tiles))
    if unknown:
        raise ValueError("map %r has no tile %s" % (world_map.map_id, ", ".join(unknown)))
    return chosen


def _tree(compiled: routes_compile.Compiled, origins: frozenset, by_days: bool):
    """(cost, days, previous) per state, searching by cost or by days."""
    key = (origins, by_days)
    cached = compiled.trees.get(key)
    if cached is not None:
        return cached
    count = len(compiled.mode_ids)
    size = len(compiled.links)
    cost, days = [INFINITY] * size, [INFINITY] * size
    previous: list = [None] * size
    queue = []
    for tile_id in sorted(origins):
        tile = compiled.tile_index[tile_id]
        for position in compiled.modes_at[tile]:
            state = tile * count + position
            cost[state], days[state] = compiled.handling[position]
            heapq.heappush(queue, (days[state] if by_days else cost[state], state))
    settled = [False] * size
    while queue:
        _priority, state = heapq.heappop(queue)
        if settled[state]:
            continue
        settled[state] = True
        here_cost, here_days = cost[state], days[state]
        tile, position = divmod(state, count)
        steps = [(to_state, here_cost + link_cost, here_days + link_days, (state, link_km, rate, False))
                 for to_state, link_cost, link_days, link_km, rate in compiled.links[state]]
        for other in compiled.modes_at[tile]:
            if other != position:
                handling_cost, handling_days = compiled.handling[other]
                steps.append((tile * count + other, here_cost + handling_cost, here_days + handling_days,
                              (state, 0.0, None, True)))
        for to_state, new_cost, new_days, how in steps:
            if settled[to_state]:
                continue
            better = new_days < days[to_state] if by_days else new_cost < cost[to_state]
            if better:
                cost[to_state], days[to_state], previous[to_state] = new_cost, new_days, how
                heapq.heappush(queue, (new_days if by_days else new_cost, to_state))
    compiled.trees[key] = (cost, days, previous)
    return compiled.trees[key]


def _best_state(compiled, tree, tile_ids, by_days):
    cost, days, _previous = tree
    count = len(compiled.mode_ids)
    metric = days if by_days else cost
    best = None
    for tile_id in tile_ids:
        tile = compiled.tile_index[tile_id]
        for position in compiled.modes_at[tile]:
            state = tile * count + position
            if metric[state] < INFINITY and (best is None or metric[state] < metric[best]):
                best = state
    return best


def _legs(compiled, tree, end_state) -> Dict[str, Any]:
    cost, days, previous = tree
    count = len(compiled.mode_ids)
    steps = []
    state = end_state
    while previous[state] is not None:
        steps.append((previous[state], state))
        state = previous[state][0]
    start_position = state % count
    steps.reverse()
    pending_cost, pending_days = compiled.handling[start_position]
    legs, inputs = [], {"labour_hours": 0.0, "feed_kg": 0.0, "fuel_kg": 0.0}
    for (from_state, km, rate, is_transfer), to_state in steps:
        position = to_state % count
        if is_transfer:
            handling_cost, handling_days = compiled.handling[position]
            pending_cost, pending_days = pending_cost + handling_cost, pending_days + handling_days
            continue
        link_cost = next(link[1] for link in compiled.links[from_state] if link[0] == to_state)
        leg = {"from": compiled.tile_ids[from_state // count], "to": compiled.tile_ids[to_state // count],
               "mode": compiled.mode_ids[position], "km": km, "days": km / rate.km_per_day,
               "cost_per_tonne": link_cost + pending_cost}
        if pending_days:
            leg["handling_days"] = pending_days
        pending_cost, pending_days = 0.0, 0.0
        legs.append(leg)
        inputs["labour_hours"] += rate.labour_hours * km
        inputs["feed_kg"] += rate.feed_kg * km
        inputs["fuel_kg"] += rate.fuel_kg * km
    return {"legs": legs, "km": sum(leg["km"] for leg in legs), "days": days[end_state],
            "cost_per_tonne": cost[end_state], "inputs": inputs}


def route(world_map: WorldMap, origin_tiles: Iterable[str], destination_tiles: Iterable[str],
          modes: Iterable[str], improvements: Optional[Mapping[str, Mapping[str, Any]]] = None,
          mode_costs: Optional[Mapping[str, float]] = None,
          handling_costs: Optional[Mapping[str, float]] = None,
          held_nodes: Optional[Iterable[str]] = None) -> Optional[Dict[str, Any]]:
    """The least-cost haul from any origin tile to any destination tile, or None.

    Returns {"legs": [{"from", "to", "mode", "km", "days", "cost_per_tonne", ("handling_days")}],
    "km", "days", "cost_per_tonne", "inputs": {labour_hours, feed_kg, fuel_kg}}. `modes` are mode ids
    (see `routes_modes.usable_modes`); `improvements` is {edge_key: {"road": true, "rail": true}}.
    `mode_costs` is money per tonne-km by mode and `handling_costs` money per tonne per change to a
    mode; without them cost is physical (labour-hours). `held_nodes` are the tech nodes the parties
    hold, which open-sea lanes may require. Origin and destination sharing a tile give no legs."""
    origins = _origin_indexes(world_map, origin_tiles)
    destinations = _origin_indexes(world_map, destination_tiles)
    if origins & destinations:
        return {"legs": [], "km": 0.0, "days": 0.0, "cost_per_tonne": 0.0,
                "inputs": {"labour_hours": 0.0, "feed_kg": 0.0, "fuel_kg": 0.0}}
    compiled = routes_compile.compiled_for(world_map, routes_modes.checked_mode_ids(world_map, modes),
                                           improvements, mode_costs, handling_costs, held_nodes)
    tree = _tree(compiled, origins, False)
    end_state = _best_state(compiled, tree, destinations, False)
    return None if end_state is None else _legs(compiled, tree, end_state)


def costs_from(world_map: WorldMap, origin_tiles: Iterable[str], modes: Iterable[str],
               improvements: Optional[Mapping[str, Mapping[str, Any]]] = None,
               mode_costs: Optional[Mapping[str, float]] = None,
               handling_costs: Optional[Mapping[str, float]] = None,
               held_nodes: Optional[Iterable[str]] = None) -> Dict[str, float]:
    """{tile: least cost per tonne from any origin tile} for every tile a haul reaches (origins cost 0).
    One search serves every destination; the tree is kept like `route`'s."""
    origins = _origin_indexes(world_map, origin_tiles)
    compiled = routes_compile.compiled_for(world_map, routes_modes.checked_mode_ids(world_map, modes),
                                           improvements, mode_costs, handling_costs, held_nodes)
    cost, _days, _previous = _tree(compiled, origins, False)
    count = len(compiled.mode_ids)
    result: Dict[str, float] = {}
    for tile_id, tile in compiled.tile_index.items():
        cheapest = min(cost[tile * count:(tile + 1) * count], default=INFINITY)
        if cheapest < INFINITY:
            result[tile_id] = cheapest
    result.update({tile_id: 0.0 for tile_id in origins})
    return result


def reach(world_map: WorldMap, origin_tiles: Iterable[str], modes: Iterable[str], days_budget: float,
          improvements: Optional[Mapping[str, Mapping[str, Any]]] = None,
          mode_costs: Optional[Mapping[str, float]] = None,
          handling_costs: Optional[Mapping[str, float]] = None,
          held_nodes: Optional[Iterable[str]] = None) -> Dict[str, float]:
    """{tile: fewest days} for every tile reachable within `days_budget` (handling days included)."""
    origins = _origin_indexes(world_map, origin_tiles)
    compiled = routes_compile.compiled_for(world_map, routes_modes.checked_mode_ids(world_map, modes),
                                           improvements, mode_costs, handling_costs, held_nodes)
    _cost, days, _previous = _tree(compiled, origins, True)
    count = len(compiled.mode_ids)
    result: Dict[str, float] = {}
    for tile_id, tile in compiled.tile_index.items():
        fewest = min((days[tile * count + position] for position in compiled.modes_at[tile]), default=INFINITY)
        if fewest <= days_budget:
            result[tile_id] = fewest
    return result


usable_modes = routes_modes.usable_modes
edge_key = routes_graph.edge_key
