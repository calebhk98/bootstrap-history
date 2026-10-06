"""What building a road or railway over one land edge takes: labour and material, from the terrain.

A built way is the caller's record (an improvement on an edge, `routes_compile`); this module prices
making one. Earthwork is a bed of the way's width and depth plus, on sloping ground, a balanced
cut-and-fill bench (a triangle of width times width times grade over four, cut equal to fill, so moved
twice), so steeper ground costs more. Surface and fixed materials come from the mode's `construction`
block in the map data; labour is the earthwork over a person-day's excavation.

Standalone: the route graph and modes of this package.
"""
from typing import Any, Dict, Optional

from sim.geography import routes_graph, routes_modes
from sim.geography.map_source import WorldMap

METRES_PER_KM = 1000.0


def land_edge(world_map: WorldMap, tile_a: str, tile_b: str) -> Optional[routes_graph.Edge]:
    """The land edge joining two tiles, or None when they do not border (or one is not on the map)."""
    key = routes_graph.edge_key(tile_a, tile_b)
    return next((edge for edge in routes_graph.graph(world_map).edges
                 if edge.edge_class == "land" and edge.key == key), None)


def requirements(world_map: WorldMap, tile_a: str, tile_b: str, improvement: str) -> Optional[Dict[str, Any]]:
    """{km, grade, trade, labour_hours, materials: {material: tonnes}, node} of building `improvement`
    (a mode's `needs_improvement`, such as "road") over the land edge, or None when it cannot be
    built there: no such edge, no mode builds it, or the ground is steeper than the mode's natural limit."""
    edge = land_edge(world_map, tile_a, tile_b)
    mode = next((entry for entry in routes_modes.modes(world_map).values()
                 if entry.get("needs_improvement") == improvement and entry.get("construction")), None)
    if edge is None or mode is None or edge.grade > mode.get("max_natural_grade", float("inf")):
        return None
    work = mode["construction"]
    km = edge.km * mode.get("km_factor", 1.0)
    metres = km * METRES_PER_KM
    width = float(work["width_m"])
    bench = width * width * edge.grade / 4.0
    earthwork_m3 = metres * (width * float(work["bed_depth_m"]) + 2.0 * bench)
    labour_hours = earthwork_m3 / float(work["excavation_m3_per_person_day"]) * float(work["work_hours_per_day"])
    surface = work["surface"]
    materials = {surface["material"]: metres * width * float(surface["depth_m"]) * float(surface["tonnes_per_m3"])}
    for material, tonnes_per_km in work.get("fixed_materials_tonnes_per_km", {}).items():
        materials[material] = materials.get(material, 0.0) + km * float(tonnes_per_km)
    return {"km": km, "grade": edge.grade, "trade": work["trade"], "labour_hours": labour_hours,
            "materials": materials, "node": mode.get("improvement_node")}
