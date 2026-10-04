"""Where a nation's people live: tiles, their carrying capacity, their share.

Any actor holding land tiles has a population per tile. Nothing here is
specific to the founder; the founder's base is just one tile.

[temporary_heuristic] A tile's share of its nation's people is its share of
the nation's cultivable capacity (arable area times fertility), on the view
that food limits where people can live. Tiles with no cultivable land hold
nobody.
"""
import functools
from typing import Dict, List, Optional, Tuple

from sim.geography import tile_holdings
from sim.geography.distance import haversine_km


def _carrying_capacity(tile_id: str) -> float:
    land = tile_holdings.tile_land(tile_id)
    return land["arable_hectares"] * land["fertility_quality_multiplier"]


@functools.lru_cache(maxsize=64)
def _capacities(home_regions: Tuple[str, ...]) -> Dict[str, float]:
    return {tile_id: _carrying_capacity(tile_id) for tile_id in tile_holdings.tiles_of_regions(home_regions)}


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
    held = _capacities(tuple(home_regions))
    if from_tile not in held or to_tile not in held:
        raise KeyError("tile not held: %s" % (from_tile if from_tile not in held else to_tile))
    return haversine_km(*tile_holdings.tile_centre(from_tile), *tile_holdings.tile_centre(to_tile))
