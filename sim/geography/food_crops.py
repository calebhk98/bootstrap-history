"""Crop energy of a tile: arable land, fertility, the climate's share of a reference yield, irrigation from rivers.

A contribution is (source_id, species_id or None, kcal per year).
"""
from typing import List, Tuple

from sim.geography import content_rules, tile_layers
from sim.geography.food_productivity import lookup
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter

HECTARES_PER_SQUARE_KM = 100.0
RIVER_BANKS = 2.0


def crop_contributions(world_map: WorldMap, tile_id: str) -> List[Tuple[str, None, float]]:
    area = tile_layers.number(world_map, tile_id, "land_area_km2", 0.0)
    arable_hectares = area * HECTARES_PER_SQUARE_KM * tile_layers.number(world_map, tile_id, "arable_fraction", 0.0)
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
    rainfed_yield = min(by_temperature, by_rain) * fertility * parameter(world_map, "food_crop_cropped_share")
    irrigated_hectares = irrigable_hectares if irrigated_yield > rainfed_yield else 0.0
    yield_factor = (irrigated_hectares * irrigated_yield
                    + max(0.0, arable_hectares - irrigated_hectares) * rainfed_yield)
    gross_tonnes = parameter(world_map, "food_crop_reference_yield") * yield_factor
    net_fraction = (1.0 - parameter(world_map, "food_crop_seed_fraction")
                    - parameter(world_map, "food_crop_loss_fraction"))
    kcal = gross_tonnes * net_fraction * parameter(world_map, "food_crop_grain_kcal_per_tonne")
    return [(parameter(world_map, "food_source_crops"), None, kcal)]
