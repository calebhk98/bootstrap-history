"""What building a road, railway or canal over one land edge takes: labour and material, from the terrain.

A built way is the caller's record (an improvement on an edge, `routes_compile`); this module prices
making one. Earthwork is a bed of the way's width and depth plus, on sloping ground, a balanced
cut-and-fill bench (a triangle of width times width times grade over four, cut equal to fill, so moved
twice), so steeper ground costs more. Ground steeper than the mode's natural limit is built engineered
(cuttings and embankments) up to the mode's engineered limit, with the bench multiplied by the mode's
earthwork factor. Surface and fixed materials come from the mode's `construction` block in the map
data; labour is the earthwork over a person-day's excavation; the build time is that labour over what
the mode's crew works in a year. Bridges and ports are in `ways_works`.

Standalone: the route graph and modes of this package.
"""
from typing import Any, Dict, Mapping, Optional

from sim.geography import routes_graph, routes_modes, ways_works
from sim.geography.map_source import WorldMap

METRES_PER_KM = 1000.0


def _mode_building(world_map: WorldMap, improvement: str) -> Optional[Dict[str, Any]]:
    return next((entry for entry in routes_modes.modes(world_map).values()
                 if entry.get("needs_improvement") == improvement and entry.get("construction")), None)


def built_km(world_map: WorldMap, improvements: Mapping[str, Mapping[str, Any]], improvement: str) -> float:
    """Length of `improvement` the caller's record holds, over the land edges it covers, counted the
    way `requirements` counts a build (a bridge's span or a port's quay for those works)."""
    if ways_works.entry(world_map, improvement) is not None:
        return ways_works.built_km(world_map, improvements, improvement)
    mode = _mode_building(world_map, improvement)
    factor = mode.get("km_factor", 1.0) if mode else 1.0
    return sum(edge.km * factor for edge in routes_graph.graph(world_map).edges
               if edge.edge_class == "land" and (improvements.get(edge.key) or {}).get(improvement))


def requirements(world_map: WorldMap, tile_a: str, tile_b: Optional[str], improvement: str) -> Optional[Dict[str, Any]]:
    """{km, grade, trade, labour_hours, materials: {material: tonnes}, node, build_years, engineered,
    crew_people, crew_hours_per_year} of building `improvement` (a mode's `needs_improvement`, such as
    "road", or a work such as "bridge" or "port") over the land edge, or None when it cannot be built
    there: no such edge, no mode builds it, or the ground is steeper than the mode's engineered limit."""
    if ways_works.entry(world_map, improvement) is not None:
        return ways_works.requirements(world_map, tile_a, tile_b, improvement)
    edge = routes_graph.land_edge(world_map, tile_a, tile_b) if tile_b is not None else None
    mode = _mode_building(world_map, improvement)
    if edge is None or mode is None:
        return None
    engineered = edge.grade > mode.get("max_natural_grade", float("inf"))
    engineering = mode.get("engineered") or {}
    if engineered and edge.grade > engineering.get("max_grade", 0.0):
        return None
    work = mode["construction"]
    km = edge.km * mode.get("km_factor", 1.0)
    metres = km * METRES_PER_KM
    width = float(work["width_m"])
    bench = width * width * edge.grade / 4.0 * (float(engineering["earthwork_factor"]) if engineered else 1.0)
    earthwork_m3 = metres * (width * float(work["bed_depth_m"]) + 2.0 * bench)
    labour_hours = earthwork_m3 / float(work["excavation_m3_per_person_day"]) * float(work["work_hours_per_day"])
    surface = work["surface"]
    materials = {surface["material"]: metres * width * float(surface["depth_m"]) * float(surface["tonnes_per_m3"])}
    for material, tonnes_per_km in work.get("fixed_materials_tonnes_per_km", {}).items():
        materials[material] = materials.get(material, 0.0) + km * float(tonnes_per_km)
    return {"km": km, "grade": edge.grade, "trade": work["trade"], "labour_hours": labour_hours,
            "materials": materials, "node": mode.get("improvement_node"), "engineered": engineered,
            **ways_works.crew_figures(work, labour_hours)}
