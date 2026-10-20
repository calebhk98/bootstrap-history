"""The crew hours a carriage mode spends per tonne-km on level ground, and which trade works them.

The numbers are `routes_rates.compute_rate`'s: the same physical inputs the route search prices a haul
with, so what the labour package counts as carriage need is what a haul costs. A mode names its
`crew_trade` in the map data; a mode with none is left out.

Standalone: the map's modes and `routes_rates`.
"""
from typing import Any, Dict, Iterable, Optional

from sim.geography import routes_carriers, routes_modes, routes_rates
from sim.geography.map_source import WorldMap


def carriage_rates(world_map: WorldMap, mode_ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """{mode_id: {carriers, tonne_km_per_team_day, team_payload_tonnes, team_days_per_tonne_km, carrier_days_per_tonne_km, crew_trade, crew_hours_per_tonne_km, cost_hours_per_tonne_km, handling_hours_per_tonne, edge_classes}} for each
    named mode with a crew trade and a rate on level, still ground or water."""
    known = routes_modes.modes(world_map)
    found: Dict[str, Dict[str, Any]] = {}
    for mode_id in sorted(routes_modes.checked_mode_ids(world_map, mode_ids)):
        mode = known[mode_id]
        if not mode.get("crew_trade"):
            continue
        rate = _level_rate(world_map, mode)
        if rate is None:
            continue
        team = routes_carriers.team_of(mode)
        found[mode_id] = {"carriers": [list(each) for each in team[0]] if team else [],
                          "tonne_km_per_team_day": team[1] if team else 0.0,
                          "team_payload_tonnes": team[2] if team else 0.0,
                          "team_days_per_tonne_km": rate.team_days,
                          "carrier_days_per_tonne_km": [list(each) for each in rate.carrier_days],
                          "crew_trade": mode["crew_trade"],
                          "crew_hours_per_tonne_km": rate.labour_hours,
                          "cost_hours_per_tonne_km": routes_rates.physical_cost(world_map, rate),
                          "handling_hours_per_tonne": float(mode.get("handling_hours_per_tonne", 0.0)),
                          "edge_classes": list(mode["edge_classes"]),
                          "needs_improvement": mode.get("needs_improvement")}
    return found


def _level_rate(world_map: WorldMap, mode: Dict[str, Any]) -> Optional[routes_rates.Rate]:
    for edge_class in mode["edge_classes"]:
        rate = routes_rates.compute_rate(world_map, mode, edge_class, 0.0, 0.0)
        if rate is not None:
            return rate
    return None
