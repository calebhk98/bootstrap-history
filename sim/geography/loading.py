"""The geography dict (regions, located materials, reach levels, the land-tile grid), assembled from the map folder."""
import copy
from typing import Any, Dict, Optional

from sim.geography import map_source

ROOT = map_source.ROOT
TILE_GRID_PROPERTIES = ("generation_rule_summary", "tile_count", "target_tile_area_km2", "unmapped_tile_count")


def _catalogue(world_map: map_source.WorldMap, name: str) -> Dict[str, Dict[str, Any]]:
    """One catalogue as {entry_id: record}, the entry id left out of the record."""
    return {entry_id: {key: value for key, value in copy.deepcopy(entry).items() if key != "id"}
            for entry_id, entry in world_map.catalogue(name).items()}


def _region_to_tiles(tiles: Dict[str, Dict[str, Any]]) -> Dict[str, list]:
    """{region_id: sorted tile ids}: the tiles each region groups, read off the tiles' own region label."""
    grouped: Dict[str, list] = {}
    for tile_id in sorted(tiles):
        region_id = tiles[tile_id].get("old_region")
        if region_id:
            grouped.setdefault(region_id, []).append(tile_id)
    return dict(sorted(grouped.items()))


def load_geography(world_map: Optional[map_source.WorldMap] = None) -> Dict[str, Any]:
    """Where things are, not just what they cost: {regions, reach_levels, located_materials, land_tiles}.

    A fresh dict from the map (the base map, or `world_map` with its mod overlays merged), so the caller may
    edit it. Reach is computed per civilisation by `Geography`; this just hands back the raw data.
    """
    world_map = world_map if world_map is not None else map_source.load_map()
    tiles = {tile_id: {key: value for key, value in copy.deepcopy(record).items() if key != "id"}
             for tile_id, record in world_map.tiles.items()}
    properties = dict(world_map.properties, tile_count=len(tiles))
    land_tiles = {key: properties[key] for key in TILE_GRID_PROPERTIES[:3] if key in properties}
    land_tiles["tiles"] = tiles
    land_tiles["region_to_tiles"] = _region_to_tiles(tiles)
    land_tiles.update({key: properties[key] for key in TILE_GRID_PROPERTIES[3:] if key in properties})
    return {"regions": _catalogue(world_map, "regions"),
            "reach_levels": _catalogue(world_map, "reach_levels"),
            "located_materials": _catalogue(world_map, "located_materials"),
            "land_tiles": land_tiles}
