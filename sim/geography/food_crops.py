"""Crop energy of a tile: arable land, fertility, the climate's share of a reference yield, irrigation from rivers.

A contribution is (source_id, species_id or None, kcal per year).
"""
from typing import List, Mapping, Optional, Tuple

from sim.geography import content_rules, food_land, tile_layers
from sim.geography.food_productivity import lookup
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter

HECTARES_PER_SQUARE_KM = 100.0
RIVER_BANKS = 2.0


def _cropped_share(world_map: WorldMap, tile_id: str, arable_hectares: float) -> float:
    """Share of arable land cropped in a year: open fields follow the fallow rotation, land cleared from forest
    follows shifting cultivation (a few crop years, then forest fallow; Ruthenberg's R value)."""
    if arable_hectares <= 0.0:
        return 0.0
    area = tile_layers.number(world_map, tile_id, "land_area_km2", 0.0) * HECTARES_PER_SQUARE_KM
    cleared_share = min(1.0, food_land.cleared_forest_fraction(world_map, tile_id) * area / arable_hectares)
    crop_years = parameter(world_map, "food_forest_fallow_crop_years")
    shifting = crop_years / (crop_years + parameter(world_map, "food_forest_fallow_years"))
    return (1.0 - cleared_share) * parameter(world_map, "food_crop_cropped_share") + cleared_share * shifting


def crop_contributions(world_map: WorldMap, tile_id: str,
                       wild_stock: Optional[Mapping] = None) -> List[Tuple[str, None, float]]:
    area = tile_layers.number(world_map, tile_id, "land_area_km2", 0.0)
    arable_hectares = area * HECTARES_PER_SQUARE_KM * food_land.arable_fraction(world_map, tile_id)
    fertility = tile_layers.number(world_map, tile_id, "fertility_quality_multiplier", 0.0)
    reader = lookup(world_map, tile_id)
    by_temperature = content_rules.suitability(parameter(world_map, "food_crop_temperature_envelope"), reader)
    by_rain = content_rules.suitability(parameter(world_map, "food_crop_water_envelope"), reader)
    # Land a large river waters is farmable whatever the rain, on alluvium of its own fertility.
    large_river_km = tile_layers.number(world_map, tile_id, "river_km_navigable", 0.0)
    small_river_km = max(0.0, tile_layers.number(world_map, tile_id, "river_km_all", 0.0) - large_river_km)
    watered_km2 = RIVER_BANKS * (large_river_km * parameter(world_map, "food_irrigation_strip_width_km")
                                 + small_river_km * parameter(world_map, "food_small_river_strip_width_km"))
    irrigable_hectares = min(area, watered_km2) * HECTARES_PER_SQUARE_KM
    irrigated_yield = (by_temperature * parameter(world_map, "food_irrigation_yield_multiplier")
                       * max(fertility, parameter(world_map, "food_irrigated_alluvium_fertility"))
                       * parameter(world_map, "food_irrigated_cropped_share"))
    rainfed_yield = min(by_temperature, by_rain) * fertility * _cropped_share(world_map, tile_id, arable_hectares)
    irrigated_hectares = irrigable_hectares if irrigated_yield > rainfed_yield else 0.0
    yield_factor = (irrigated_hectares * irrigated_yield
                    + max(0.0, arable_hectares - irrigated_hectares) * rainfed_yield)
    gross_tonnes = parameter(world_map, "food_crop_reference_yield") * yield_factor
    net_fraction = (1.0 - parameter(world_map, "food_crop_seed_fraction")
                    - parameter(world_map, "food_crop_loss_fraction"))
    kcal = gross_tonnes * net_fraction * parameter(world_map, "food_crop_grain_kcal_per_tonne")
    return [(parameter(world_map, "food_source_crops"), None, kcal)]
