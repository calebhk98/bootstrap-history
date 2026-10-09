"""Bridges and ports: what a built work that is not a carriage mode takes, from the map's `ways` catalogue.

A bridge is recorded on the edge key of a land edge that crosses a river (tiles on the same river); a
port is recorded under the id of a coastal tile with no natural harbour. Both are priced from the volume
they place (length times section), the material that volume is made of, fixed timber, and an all-in
labour per cubic metre; the build time is the labour over what the work's crew does in a year.

Standalone: the route graph and tile layers of this package.
"""
from typing import Any, Dict, Mapping, Optional

from sim.geography import routes_graph, tile_layers
from sim.geography.map_source import WorldMap

METRES_PER_KM = 1000.0


def entry(world_map: WorldMap, improvement: str) -> Optional[Dict[str, Any]]:
    """The `ways` catalogue entry named `improvement`, or None."""
    return world_map.catalogue("ways").get(improvement)


def crew_figures(work: Mapping[str, Any], labour_hours: float) -> Dict[str, float]:
    """{crew_people, crew_hours_per_year, build_years} of a work whose construction block is `work`."""
    crew_hours_per_year = float(work["crew_people"]) * float(work["work_days_per_year"]) * float(work["work_hours_per_day"])
    return {"crew_people": float(work["crew_people"]), "crew_hours_per_year": crew_hours_per_year,
            "build_years": labour_hours / crew_hours_per_year}


def has_natural_harbour(world_map: WorldMap, tile_id: str) -> bool:
    """Whether the tile's own coast already lets ships put in (or the map has no harbour layer, so
    every coastal tile is joined to the sea)."""
    return "is_port" not in world_map.layers or bool(tile_layers.value(world_map, tile_id, "is_port"))


def requirements(world_map: WorldMap, tile_a: str, tile_b: str, improvement: str) -> Optional[Dict[str, Any]]:
    """The same record as `ways_build.requirements` for a bridge (over the land edge between two tiles
    that cross a river) or a port (on the coastal tile `tile_a`, which has no natural harbour), or None
    when it cannot be built there or `improvement` names no such work."""
    found = entry(world_map, improvement)
    if found is None:
        return None
    if found["type"] == "crossing":
        edge = routes_graph.land_edge(world_map, tile_a, tile_b)
        if edge is None or not edge.crosses_river:
            return None
    elif (tile_a not in world_map.tiles or tile_b not in (None, tile_a)
          or not world_map.tiles[tile_a].get("coastal") or has_natural_harbour(world_map, tile_a)):
        return None
    work = found["construction"]
    volume_m3 = float(work["length_m"]) * float(work["section_m2"])
    labour_hours = volume_m3 * float(work["person_days_per_m3"]) * float(work["work_hours_per_day"])
    materials = {work["material"]: volume_m3 * float(work["tonnes_per_m3"])}
    for material, tonnes in work.get("fixed_materials_tonnes", {}).items():
        materials[material] = materials.get(material, 0.0) + float(tonnes)
    return {"km": float(work["length_m"]) / METRES_PER_KM, "grade": 0.0, "trade": work["trade"],
            "labour_hours": labour_hours, "materials": materials, "node": found.get("improvement_node"),
            "engineered": False, **crew_figures(work, labour_hours)}


def key_of(world_map: WorldMap, improvement: str, tile_a: str, tile_b: str) -> str:
    """The key `improvement` is recorded under: the tile id for a harbour, the edge key otherwise."""
    found = entry(world_map, improvement)
    return tile_a if found is not None and found["type"] == "harbour" else routes_graph.edge_key(tile_a, tile_b)


def built_km(world_map: WorldMap, improvements: Mapping[str, Mapping[str, Any]], improvement: str) -> float:
    """Length of `improvement` (a bridge's span, a port's quay) the record holds."""
    found = entry(world_map, improvement)
    if found is None:
        return 0.0
    count = sum(1 for built in improvements.values() if built.get(improvement))
    return count * float(found["construction"]["length_m"]) / METRES_PER_KM
