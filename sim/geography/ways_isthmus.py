"""Canals across an isthmus: a cut that joins two seas, from the map's `isthmuses` catalogue.

An isthmus entry states where a cut is physically possible (the two tiles it joins, its length, the mean
height of the ground it goes through, how far its banks spread). The work is the earth in the cut's section
(the water depth of the canal mode plus the ground height, times the width and the banks' spread) over the
cut's length, at the labour rates, crew and lining of the route mode the entry builds like. A built cut is
recorded under the pair's edge key like any other way and is a sea link of the cut's length.

Standalone: the route graph and modes of this package.
"""
from typing import Any, Dict, List, Optional

from sim.geography import routes_graph, routes_modes
from sim.geography.map_source import WorldMap
from sim.geography.ways_works import crew_figures

METRES_PER_KM = 1000.0
CUT_FIELDS = ("way", "tile_a", "tile_b", "length_km", "mean_ground_height_m", "side_slope_run_per_rise", "builds_like")


def sites(world_map: WorldMap) -> List[Dict[str, Any]]:
    return [world_map.catalogue("isthmuses")[site_id] for site_id in sorted(world_map.catalogue("isthmuses"))]


def is_cut_way(world_map: WorldMap, improvement: str) -> bool:
    """Whether `improvement` is a way some isthmus entry builds."""
    return any(site["way"] == improvement for site in sites(world_map))


def site_between(world_map: WorldMap, improvement: str, tile_a: str, tile_b: Optional[str]) -> Optional[Dict[str, Any]]:
    """The isthmus entry for `improvement` that joins the two tiles (either order), or None."""
    pair = {tile_a, tile_b}
    return next((site for site in sites(world_map)
                 if site["way"] == improvement and {site["tile_a"], site["tile_b"]} == pair), None)


def requirements(world_map: WorldMap, tile_a: str, tile_b: Optional[str], improvement: str) -> Optional[Dict[str, Any]]:
    """The same record as `ways_build.requirements` for a cut between the two tiles, or None when no isthmus
    is declared between them."""
    site = site_between(world_map, improvement, tile_a, tile_b)
    mode = routes_modes.modes(world_map).get(site["builds_like"]) if site else None
    if mode is None or not mode.get("construction"):
        return None
    work = mode["construction"]
    metres = float(site["length_km"]) * METRES_PER_KM
    depth = float(work["bed_depth_m"]) + float(site["mean_ground_height_m"])
    section_m2 = depth * (float(work["width_m"]) + float(site["side_slope_run_per_rise"]) * depth)
    labour_hours = metres * section_m2 / float(work["excavation_m3_per_person_day"]) * float(work["work_hours_per_day"])
    lining = work["surface"]
    materials = {lining["material"]: metres * float(work["width_m"]) * float(lining["depth_m"]) * float(lining["tonnes_per_m3"])}
    for material, tonnes_per_km in work.get("fixed_materials_tonnes_per_km", {}).items():
        materials[material] = materials.get(material, 0.0) + float(site["length_km"]) * float(tonnes_per_km)
    return {"km": float(site["length_km"]), "grade": 0.0, "trade": work["trade"], "labour_hours": labour_hours,
            "materials": materials, "node": mode.get("improvement_node"), "engineered": False,
            **crew_figures(work, labour_hours)}


def built_km(world_map: WorldMap, improvements, improvement: str) -> float:
    """Length of the cuts of `improvement` the record holds."""
    return sum(float(site["length_km"]) for site in sites(world_map) if site["way"] == improvement
               and (improvements.get(routes_graph.edge_key(site["tile_a"], site["tile_b"])) or {}).get(improvement))


def cut_edges(world_map: WorldMap, improvements) -> List[routes_graph.Edge]:
    """The sea edges built cuts open: one per built cut, as long as the cut."""
    return [routes_graph.Edge(site["tile_a"], site["tile_b"], "coast", float(site["length_km"]))
            for site in sites(world_map)
            if site["tile_a"] in world_map.tiles and site["tile_b"] in world_map.tiles
            and ((improvements or {}).get(routes_graph.edge_key(site["tile_a"], site["tile_b"])) or {}).get(site["way"])]


def invalid_entries(world_map: WorldMap) -> List[str]:
    """Ids of isthmus entries missing a field, a source or a reason, or naming a tile or mode the map lacks."""
    modes = routes_modes.modes(world_map)
    return [site_id for site_id, site in sorted(world_map.catalogue("isthmuses").items())
            if any(field not in site for field in CUT_FIELDS) or not site.get("source") or not site.get("why")
            or site["tile_a"] not in world_map.tiles or site["tile_b"] not in world_map.tiles
            or site["builds_like"] not in modes or float(site["length_km"]) <= 0.0]
