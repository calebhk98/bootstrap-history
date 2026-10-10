"""Where a nation's people live: tiles, their carrying capacity, their share.

Any actor holding land tiles has a population per tile. Nothing here is
specific to the founder; the founder's base is just one tile.

A tile's share of its nation's people is its share of the nation's food
potential: the sustainable food energy the tile's crops, herds, game, wild
plants and fish give (`food_potential`, the land at a full stock), on the view
that food limits where people can live. Tiles that give no food hold nobody.
"""
import functools
from typing import Dict, List, Optional, Tuple

from sim.geography import queries, tile_holdings
from sim.geography.distance import haversine_km


@functools.lru_cache(maxsize=2048)
def _carrying_capacity(tile_id: str) -> float:
    return float(queries.food_potential(tile_id)["total_kcal_per_year"])


@functools.lru_cache(maxsize=64)
def _capacities(held_tiles: Tuple[str, ...]) -> Dict[str, float]:
    return {tile_id: _carrying_capacity(tile_id) for tile_id in held_tiles}


@functools.lru_cache(maxsize=64)
def _summary(held_tiles: Tuple[str, ...]) -> Tuple[Tuple[str, ...], float, float, Optional[str]]:
    """(sorted tile ids, total capacity, best tile's capacity, default base tile)."""
    capacities = _capacities(held_tiles)
    default = (min(capacities, key=lambda tile_id: (-capacities[tile_id], tile_id))
               if capacities else None)
    return (tuple(sorted(capacities)), sum(capacities.values()),
            max(capacities.values(), default=0.0), default)


def tile_ids(held_tiles: List[str]) -> List[str]:
    return list(_summary(tuple(held_tiles))[0])


def population_share(held_tiles: List[str], tile_id: str) -> float:
    """Fraction of the nation's people living on `tile_id` (0 if not held)."""
    total = _summary(tuple(held_tiles))[1]
    if total <= 0.0:
        return 0.0
    return _capacities(tuple(held_tiles)).get(tile_id, 0.0) / total


def relative_capacity(held_tiles: List[str], tile_id: str) -> float:
    """Capacity of `tile_id` as a fraction of the nation's best tile."""
    best = _summary(tuple(held_tiles))[2]
    if best <= 0.0:
        return 0.0
    return _capacities(tuple(held_tiles)).get(tile_id, 0.0) / best


def default_base_tile(held_tiles: List[str]) -> Optional[str]:
    """The best-endowed tile, ties broken by id."""
    return _summary(tuple(held_tiles))[3]


def distance_km(held_tiles: List[str], from_tile: str, to_tile: str) -> float:
    """Great-circle distance between two held tiles' centres."""
    held = _capacities(tuple(held_tiles))
    if from_tile not in held or to_tile not in held:
        raise KeyError("tile not held: %s" % (from_tile if from_tile not in held else to_tile))
    return haversine_km(*tile_holdings.tile_centre(from_tile), *tile_holdings.tile_centre(to_tile))


def capacity_kcal_per_day(tile_id: str) -> float:
    """The food energy a day a tile's land gives at a full stock: what a settlement there can live on at most."""
    return _carrying_capacity(tile_id) / 365.0


def worked_kcal_per_day(tile_id: str, hectares_worked: float) -> float:
    """The food energy a day the people working `hectares_worked` of a tile bring in: the tile's full yield over its
    whole land, in the share of that land they work."""
    land_hectares = tile_holdings.tile_land(tile_id)["land_area_km2"] * tile_holdings.HECTARES_PER_KM2
    if land_hectares <= 0.0:
        return 0.0
    return capacity_kcal_per_day(tile_id) * min(1.0, max(0.0, hectares_worked) / land_hectares)


def candidate_tiles(held_tiles: List[str], claimed_tiles: List[str], by_sea: bool = False) -> List[str]:
    """Tiles a settlement could be sent to, best land first (ties by id): tiles nobody holds that border a tile
    already held or claimed, and, when the voyage is by sea, coastal tiles when a held or claimed tile is coastal."""
    taken = set(held_tiles) | set(claimed_tiles)
    world_map = tile_holdings._map(None)
    reachable = {neighbour for tile_id in taken for neighbour in tile_holdings.neighbours(tile_id, world_map)}
    if by_sea and any(world_map.tiles[tile_id].get("coastal") for tile_id in taken if tile_id in world_map.tiles):
        reachable |= {tile_id for tile_id, tile in world_map.tiles.items() if tile.get("coastal")}
    found = [tile_id for tile_id in reachable - taken
             if tile_id in world_map.tiles and _carrying_capacity(tile_id) > 0.0]
    return sorted(found, key=lambda tile_id: (-_carrying_capacity(tile_id), tile_id))


def distance_between_tiles_km(from_tile: str, to_tile: str) -> float:
    """Great-circle distance between two tiles' centres, held or not."""
    return haversine_km(*tile_holdings.tile_centre(from_tile), *tile_holdings.tile_centre(to_tile))
