"""Find the land tile that holds a position.

References into the tile grid (a deposit, later a town) carry a latitude and
longitude, never a tile id, so regenerating the grid at another cell size
leaves them valid. Standalone: no engine, no data files.
"""
import functools
import json
import math
import os
from typing import Any, Dict, Optional, Tuple


def _unit_vector(latitude: float, longitude: float) -> Tuple[float, float, float]:
    latitude_radians = math.radians(latitude)
    longitude_radians = math.radians(longitude)
    return (math.cos(latitude_radians) * math.cos(longitude_radians),
            math.cos(latitude_radians) * math.sin(longitude_radians),
            math.sin(latitude_radians))


def nearest_tile_id(tiles: Dict[str, Dict[str, Any]], latitude: float,
                    longitude: float) -> Optional[str]:
    """Id of the tile whose centre is nearest the position on the sphere
    (ties go to the lowest id, so the answer is deterministic)."""
    target_x, target_y, target_z = _unit_vector(latitude, longitude)
    best_id = None
    best_alignment = -2.0
    for tile_id in sorted(tiles):
        tile = tiles[tile_id]
        tile_x, tile_y, tile_z = _unit_vector(tile["lat"], tile["lon"])
        alignment = tile_x * target_x + tile_y * target_y + tile_z * target_z
        if alignment > best_alignment:
            best_id, best_alignment = tile_id, alignment
    return best_id


def region_of_tile(geography: Dict[str, Any]) -> Dict[str, str]:
    """{tile_id: region_id} for every tile a region groups."""
    region_to_tiles = geography.get("land_tiles", {}).get("region_to_tiles", {})
    return {tile_id: region_id
            for region_id, tile_ids in region_to_tiles.items()
            for tile_id in tile_ids}


_GEOGRAPHY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "world", "geography.json")


@functools.lru_cache(maxsize=None)
def tile_holding(latitude: float, longitude: float) -> Optional[str]:
    """The shipped grid's tile that holds this position."""
    with open(_GEOGRAPHY_FILE) as handle:
        tiles = json.load(handle)["land_tiles"]["tiles"]
    return nearest_tile_id(tiles, latitude, longitude)
