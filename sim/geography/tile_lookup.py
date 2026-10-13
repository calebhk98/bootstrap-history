"""Find the land tile that holds a position.

References into the tile grid (a deposit, later a town) carry a latitude and
longitude, never a tile id, so regenerating the grid at another cell size
leaves them valid. Standalone: no engine; positions resolve against the base map.
"""
import functools
import math
from typing import Any, Dict, Optional, Tuple

from sim.geography import map_source


def _unit_vector(latitude: float, longitude: float) -> Tuple[float, float, float]:
    latitude_radians = math.radians(latitude)
    longitude_radians = math.radians(longitude)
    return (math.cos(latitude_radians) * math.cos(longitude_radians),
            math.cos(latitude_radians) * math.sin(longitude_radians),
            math.sin(latitude_radians))


_centres: list = []    # [tiles, size, sorted (tile id, unit vector) pairs] of the last tile set looked up


def _tile_centres(tiles: Dict[str, Dict[str, Any]]):
    """(tile id, unit vector of its centre) in id order, kept while the same tile set is asked again."""
    if _centres and _centres[0] is tiles and _centres[1] == len(tiles):
        return _centres[2]
    centres = [(tile_id, _unit_vector(tiles[tile_id]["lat"], tiles[tile_id]["lon"])) for tile_id in sorted(tiles)]
    _centres[:] = [tiles, len(tiles), centres]
    return centres


def nearest_tile_id(tiles: Dict[str, Dict[str, Any]], latitude: float,
                    longitude: float) -> Optional[str]:
    """Id of the tile whose centre is nearest the position on the sphere
    (ties go to the lowest id, so the answer is deterministic)."""
    target_x, target_y, target_z = _unit_vector(latitude, longitude)
    best_id = None
    best_alignment = -2.0
    for tile_id, (tile_x, tile_y, tile_z) in _tile_centres(tiles):
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


@functools.lru_cache(maxsize=None)
def tile_holding(latitude: float, longitude: float) -> Optional[str]:
    """The base map's tile that holds this position."""
    return nearest_tile_id(map_source.load_map().tiles, latitude, longitude)
