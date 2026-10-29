"""Where a place is: a tile or a region id of the geography file, and the distance between two."""
import functools
from typing import Optional, Tuple

from sim.geography import regions
from sim.geography.distance import haversine_km
from sim.geography.loading import load_geography


@functools.lru_cache(maxsize=None)
def place_coordinates(place: str) -> Optional[Tuple[float, float]]:
    """(latitude, longitude) of a tile, or of a region's anchor; None when the id is on neither list."""
    land = load_geography()["land_tiles"]
    tile = land["tiles"].get(place)
    if tile is not None:
        return float(tile["lat"]), float(tile["lon"])
    if place in land["region_to_tiles"]:
        return regions.region_anchor(load_geography(), place)
    return None


def distance_between_places(place_a: str, place_b: str) -> float:
    """Great-circle kilometres between two places; 0 when either is not on the map."""
    first, second = place_coordinates(place_a), place_coordinates(place_b)
    if first is None or second is None:
        return 0.0
    return haversine_km(first[0], first[1], second[0], second[1])
