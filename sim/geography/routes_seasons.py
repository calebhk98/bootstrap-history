"""Seasonal closure of route modes, as expected days of waiting per haul over an edge.

A route mode may carry `closures`, a list of rules: {id, closed_days_per_year, wait_span_km, kind,
conf, source, why} plus optional conditions that must all hold on the edge: `edge_classes`, `box`
(lat/lon of the edge midpoint), `coldest_month_c_below` (the colder end tile) and
`elevation_m_above` (the higher end tile). Where several rules hold the longest closure applies.

The economy is yearly, so there is no calendar: a haul arrives on a uniformly random day, finds the
edge shut with chance closed/365 and then waits half the closure on average. One wait is paid per
passage, not per hop, so an edge pays its share (km over `wait_span_km`, at most all) of it.

Standalone: the route graph and tile layers of this package.
"""
from typing import Any, Dict, Optional, Tuple

from sim.geography import routes_graph, tile_layers
from sim.geography.map_source import WorldMap
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR as DAYS_PER_YEAR


def expected_wait_days(closed_days: float, km: float, span_km: float) -> float:
    """Expected days a haul over `km` of an edge shut `closed_days` a year waits for it to open."""
    if closed_days <= 0.0:
        return 0.0
    return closed_days / DAYS_PER_YEAR * closed_days / 2.0 * min(1.0, km / span_km)


def _tile_numbers(world_map: WorldMap, edge: routes_graph.Edge, layer: str):
    return [value for value in (tile_layers.number(world_map, tile, layer) for tile in (edge.tile_a, edge.tile_b))
            if value is not None]


def _holds(world_map: WorldMap, edge: routes_graph.Edge, rule: Dict[str, Any], middle) -> bool:
    if "edge_classes" in rule and edge.edge_class not in rule["edge_classes"]:
        return False
    box = rule.get("box")
    if box is not None:
        if not (box["lat_min"] <= middle[0] <= box["lat_max"] and box["lon_min"] <= middle[1] <= box["lon_max"]):
            return False
    if "coldest_month_c_below" in rule:
        coldest = _tile_numbers(world_map, edge, "coldest_month_temperature_c")
        if not coldest or min(coldest) >= rule["coldest_month_c_below"]:
            return False
    if "elevation_m_above" in rule:
        heights = _tile_numbers(world_map, edge, "elevation_mean_m")
        if not heights or max(heights) <= rule["elevation_m_above"]:
            return False
    return True


def wait_days(world_map: WorldMap, mode: Dict[str, Any], edge: routes_graph.Edge, km: float) -> float:
    """Expected days of waiting for the season that a haul by `mode` over `km` of `edge` pays (0 when open)."""
    rules = mode.get("closures")
    if not rules:
        return 0.0
    middle: Optional[Tuple[float, float]] = edge.middle
    if middle is None and any("box" in rule for rule in rules):
        middle = routes_graph.midpoint_of(world_map, edge)
    worst = None
    for rule in rules:
        if _holds(world_map, edge, rule, middle) and (
                worst is None or rule["closed_days_per_year"] > worst["closed_days_per_year"]):
            worst = rule
    if worst is None:
        return 0.0
    return expected_wait_days(worst["closed_days_per_year"], km, worst["wait_span_km"])
