"""Where a nation's people live: tiles, their carrying capacity, their share.

Any actor holding land tiles has a population per tile. Nothing here is
specific to the founder; the founder's base is just one tile.

[temporary_heuristic] A tile's share of its nation's people is its share of
the nation's cultivable capacity (arable area times fertility), on the view
that food limits where people can live. Tiles with no cultivable land hold
nobody.
"""
import functools
import math
from typing import Dict, List, Optional, Tuple

from sim.world import land


def _carrying_capacity(tile_land) -> float:
    return tile_land.arable_iugera * tile_land.fertility_quality_multiplier


@functools.lru_cache(maxsize=64)
def _capacities(home_regions: Tuple[str, ...]) -> Dict[str, float]:
    geography = land._load_json(land.GEOGRAPHY_FILE)
    tile_lands = land.load_tile_lands(geography)
    tile_ids = land._tile_ids_for_home_regions(
        list(home_regions), geography.get("land_tiles", {}))
    return {tile_id: _carrying_capacity(tile_lands[tile_id])
            for tile_id in tile_ids if tile_id in tile_lands}


@functools.lru_cache(maxsize=64)
def _tile_centres(home_regions: Tuple[str, ...]) -> Dict[str, Tuple[float, float]]:
    geography = land._load_json(land.GEOGRAPHY_FILE)
    tiles = geography.get("land_tiles", {}).get("tiles", {})
    return {tile_id: (tiles[tile_id]["lat"], tiles[tile_id]["lon"])
            for tile_id in _capacities(home_regions)}


@functools.lru_cache(maxsize=64)
def _summary(home_regions: Tuple[str, ...]) -> Tuple[Tuple[str, ...], float, float, Optional[str]]:
    """(sorted tile ids, total capacity, best tile's capacity, default base tile)."""
    capacities = _capacities(home_regions)
    default = (min(capacities, key=lambda tile_id: (-capacities[tile_id], tile_id))
               if capacities else None)
    return (tuple(sorted(capacities)), sum(capacities.values()),
            max(capacities.values(), default=0.0), default)


def tile_ids(home_regions: List[str]) -> List[str]:
    return list(_summary(tuple(home_regions))[0])


def population_share(home_regions: List[str], tile_id: str) -> float:
    """Fraction of the nation's people living on `tile_id` (0 if not held)."""
    total = _summary(tuple(home_regions))[1]
    if total <= 0.0:
        return 0.0
    return _capacities(tuple(home_regions)).get(tile_id, 0.0) / total


def relative_capacity(home_regions: List[str], tile_id: str) -> float:
    """Capacity of `tile_id` as a fraction of the nation's best tile."""
    best = _summary(tuple(home_regions))[2]
    if best <= 0.0:
        return 0.0
    return _capacities(tuple(home_regions)).get(tile_id, 0.0) / best


def default_base_tile(home_regions: List[str]) -> Optional[str]:
    """The best-endowed tile, ties broken by id."""
    return _summary(tuple(home_regions))[3]


def distance_km(home_regions: List[str], from_tile: str, to_tile: str) -> float:
    """Great-circle distance between two held tiles' centres."""
    centres = _tile_centres(tuple(home_regions))
    lat_from, lon_from = centres[from_tile]
    lat_to, lon_to = centres[to_tile]
    earth_radius_km = 6371.0
    phi_from, phi_to = math.radians(lat_from), math.radians(lat_to)
    delta_phi = phi_to - phi_from
    delta_lambda = math.radians(lon_to - lon_from)
    half_chord = (math.sin(delta_phi / 2) ** 2
                  + math.cos(phi_from) * math.cos(phi_to) * math.sin(delta_lambda / 2) ** 2)
    return 2 * earth_radius_km * math.asin(min(1.0, math.sqrt(half_chord)))
