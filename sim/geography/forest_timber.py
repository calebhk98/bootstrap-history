"""The standing timber of a tile: a stock that felling draws down and growth restores.

The game keeps {tile id: tonnes felled below the tile's full stock}; a missing entry is an untouched forest.
A tile's stock and its yearly increment both come from its net primary production and its forest area, so
climate sets them. Pure helpers only; the engine draws and regrows the saved dictionary each year.
"""
import math
from typing import Dict, Mapping, Optional

from sim.geography import food_land, food_productivity, tile_layers
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter

HECTARES_PER_SQUARE_KM = 100.0
TONNES_PER_HECTARE_PER_GRAM_PER_SQUARE_METRE = 0.01   # one gram per square metre is a hundredth of a tonne a hectare


def forest_hectares(world_map: WorldMap, tile_id: str) -> float:
    """Hectares of the tile under forest that the plough has not taken."""
    area = tile_layers.number(world_map, tile_id, "land_area_km2", 0.0) * HECTARES_PER_SQUARE_KM
    forest = tile_layers.number(world_map, tile_id, "forest_fraction", 0.0)
    return area * max(0.0, forest - food_land.cleared_forest_fraction(world_map, tile_id))


def increment_tonnes_per_hectare_year(world_map: WorldMap, tile_id: str) -> float:
    """Air-dry stem wood a hectare of the tile's forest grows in a year."""
    dry = food_productivity.net_primary_production(world_map, tile_id) * TONNES_PER_HECTARE_PER_GRAM_PER_SQUARE_METRE
    return dry * parameter(world_map, "forest_stem_share_of_npp") * parameter(world_map, "forest_air_dry_mass_per_dry_mass")


def full_tonnes_per_hectare(world_map: WorldMap, tile_id: str) -> float:
    """Air-dry stem wood a hectare of untouched forest holds standing."""
    return increment_tonnes_per_hectare_year(world_map, tile_id) * parameter(world_map, "forest_standing_years_of_stem_increment")


def full_tonnes(world_map: WorldMap, tile_id: str) -> float:
    """Tonnes the tile's forest holds untouched."""
    cache = food_productivity.food_cache(world_map, "timber_full")
    if tile_id not in cache:
        cache[tile_id] = forest_hectares(world_map, tile_id) * full_tonnes_per_hectare(world_map, tile_id)
    return cache[tile_id]


def regrowth_tonnes_per_year(world_map: WorldMap, tile_id: str) -> float:
    """Tonnes a year the tile's forest regrows into what has been felled."""
    cache = food_productivity.food_cache(world_map, "timber_regrowth")
    if tile_id not in cache:
        cache[tile_id] = forest_hectares(world_map, tile_id) * increment_tonnes_per_hectare_year(world_map, tile_id)
    return cache[tile_id]


def standing_tonnes(world_map: WorldMap, felled: Optional[Mapping[str, float]], tile_id: str) -> float:
    """Tonnes standing on the tile now."""
    return max(0.0, full_tonnes(world_map, tile_id) - (felled or {}).get(tile_id, 0.0))


def fell(world_map: WorldMap, felled: Mapping[str, float], tile_id: str, tonnes: float) -> Dict[str, float]:
    """The felled ledger after `tonnes` come off the tile, never more than stands there."""
    taken = min(max(0.0, tonnes), standing_tonnes(world_map, felled, tile_id))
    after = dict(felled)
    if taken > 0.0:
        after[tile_id] = after.get(tile_id, 0.0) + taken
    return after


def regrow(world_map: WorldMap, felled: Mapping[str, float]) -> Dict[str, float]:
    """The felled ledger a year on: each tile regrows at its increment until its stock is whole."""
    after = {}
    for tile_id, tonnes in felled.items():
        left = tonnes - regrowth_tonnes_per_year(world_map, tile_id)
        if left > 1e-9:
            after[tile_id] = left
    return after


def felled_radius_km(world_map: WorldMap, felled: Optional[Mapping[str, float]], tile_id: str) -> float:
    """How far the nearest standing wood lies: the felled area is a disc around the settlement, so the
    haul grows with the square root of the area cut."""
    cut = (felled or {}).get(tile_id, 0.0)
    per_hectare = full_tonnes_per_hectare(world_map, tile_id)
    if cut <= 0.0 or per_hectare <= 0.0:
        return 0.0
    return math.sqrt(cut / per_hectare / HECTARES_PER_SQUARE_KM / math.pi)


def mean_increment_tonnes_per_hectare_year(world_map: WorldMap, tile_ids) -> float:
    """The increment per hectare over these tiles' forest, weighted by forest area (0 where there is none)."""
    hectares = [(forest_hectares(world_map, tile_id), tile_id) for tile_id in tile_ids]
    total = sum(area for area, _tile_id in hectares)
    if total <= 0.0:
        return 0.0
    return sum(area * increment_tonnes_per_hectare_year(world_map, tile_id) for area, tile_id in hectares) / total
