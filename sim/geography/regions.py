"""Regions as named groups of tiles: a derived view, never a second source.

`the map folder (data/world/geography/)` keeps for each region only what a tile cannot
say: its name and a note. Area, arable land and fertility are sums over the region's tiles
(`land.load_region_lands`); reach and mineral access are read per tile. Standalone: data files only.
"""
import math
from typing import Any, Dict, Tuple

from sim.geography import tile_lookup


region_of_tile = tile_lookup.region_of_tile


def region_anchor(geography: Dict[str, Any], region_id: str) -> Tuple[float, float]:
    """(latitude, longitude) of the land-area-weighted centre of the region's
    tiles, taken on the sphere so the answer is right across the date line."""
    tiles = geography["land_tiles"]["tiles"]
    sum_x = sum_y = sum_z = 0.0
    for tile_id in geography["land_tiles"]["region_to_tiles"][region_id]:
        tile = tiles[tile_id]
        latitude, longitude = math.radians(tile["lat"]), math.radians(tile["lon"])
        area = tile["land_area_km2"]
        sum_x += area * math.cos(latitude) * math.cos(longitude)
        sum_y += area * math.cos(latitude) * math.sin(longitude)
        sum_z += area * math.sin(latitude)
    return (math.degrees(math.atan2(sum_z, math.hypot(sum_x, sum_y))),
            math.degrees(math.atan2(sum_y, sum_x)))


def region_records(geography: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """{region_id: label record plus the anchor point derived from its tiles}."""
    return {region_id: dict(record, **dict(zip(("lat", "lon"), region_anchor(geography, region_id))))
            for region_id, record in geography.get("regions", {}).items()
            if not region_id.startswith("_")}
