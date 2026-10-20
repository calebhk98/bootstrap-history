"""Crop land of a tile: how much of it a plough can crop in a year, and how well the soil, climate and rivers
let a cropped hectare yield against the reference field (ordinary open-field soil and climate, factor one).

The physical yield of a reference hectare, its seed, loss and energy come from the farm model through a
`CropTechnique` the caller supplies (the actor's crop, tools and rotation); this module owns only the tile's side.
A contribution is (source_id, species_id or None, kcal per year).
"""
from typing import List, Mapping, NamedTuple, Optional, Tuple

from sim.geography import content_rules, food_land, tile_layers
from sim.geography.food_productivity import lookup
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter

HECTARES_PER_SQUARE_KM = 100.0
RIVER_BANKS = 2.0


class CropTechnique(NamedTuple):
    """What the farm model says one cropped reference hectare gives, and how much land the rotation crops."""
    kg_per_cropped_hectare: float       # gross harvest of the reference field at the technique's reference labour
    open_field_cropped_share: float     # share of open arable land cropped in a year (one less the fallow share)
    seed_kg_per_cropped_hectare: float  # kept back for sowing, whatever the harvest
    loss_fraction: float                # share lost between field and meal
    kcal_per_kg: float


class CropSite(NamedTuple):
    arable_hectares: float
    cropped_hectares: float             # hectares cropped in a year: fallow rotation, shifting cultivation, flood land
    yield_factor: float                 # mean yield of a cropped hectare against the reference field


def _rainfed_cropped_share(world_map: WorldMap, tile_id: str, arable_hectares: float,
                           open_field_cropped_share: float) -> float:
    """Share of rainfed arable land cropped in a year: open fields follow the fallow rotation, land cleared from
    forest follows shifting cultivation (a few crop years, then forest fallow; Ruthenberg's R value)."""
    if arable_hectares <= 0.0:
        return 0.0
    area = tile_layers.number(world_map, tile_id, "land_area_km2", 0.0) * HECTARES_PER_SQUARE_KM
    cleared_share = min(1.0, food_land.cleared_forest_fraction(world_map, tile_id) * area / arable_hectares)
    crop_years = parameter(world_map, "food_forest_fallow_crop_years")
    shifting = crop_years / (crop_years + parameter(world_map, "food_forest_fallow_years"))
    return (1.0 - cleared_share) * open_field_cropped_share + cleared_share * shifting


def crop_site(world_map: WorldMap, tile_id: str, open_field_cropped_share: float, nutrient_factor: float = 1.0) -> CropSite:
    """The tile's cropland under a rotation that crops `open_field_cropped_share` of open fields each year.
    `nutrient_factor` is what the tile's soil nitrogen stock does to a cropped hectare's yield (sim/geography/soil_nutrients.py)."""
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
    irrigated_quality = (by_temperature * parameter(world_map, "food_irrigation_yield_multiplier")
                         * max(fertility, parameter(world_map, "food_irrigated_alluvium_fertility")))
    irrigated_cropped_share = parameter(world_map, "food_irrigated_cropped_share")
    rainfed_quality = min(by_temperature, by_rain) * fertility
    rainfed_cropped_share = _rainfed_cropped_share(world_map, tile_id, arable_hectares, open_field_cropped_share)
    irrigated = irrigable_hectares if irrigated_quality * irrigated_cropped_share > rainfed_quality * rainfed_cropped_share \
        else 0.0
    rainfed = max(0.0, arable_hectares - irrigated)
    cropped = irrigated * irrigated_cropped_share + rainfed * rainfed_cropped_share
    if cropped <= 0.0:
        return CropSite(arable_hectares, 0.0, 0.0)
    harvest_weight = irrigated * irrigated_cropped_share * irrigated_quality + rainfed * rainfed_cropped_share * rainfed_quality
    return CropSite(arable_hectares, cropped, harvest_weight / cropped * nutrient_factor)


def crop_contributions(world_map: WorldMap, tile_id: str, wild_stock: Optional[Mapping] = None,
                       crop_technique: Optional[CropTechnique] = None,
                       nutrient_factors: Optional[Mapping[str, float]] = None) -> List[Tuple[str, None, float]]:
    """Net food energy of the tile's crops: the farm model's gross harvest of a reference hectare, on the
    cropped hectares at the tile's yield factor, less seed and loss. No technique, no crop source."""
    if crop_technique is None:
        return []
    site = crop_site(world_map, tile_id, crop_technique.open_field_cropped_share, (nutrient_factors or {}).get(tile_id, 1.0))
    gross_kg = crop_technique.kg_per_cropped_hectare * site.cropped_hectares * site.yield_factor
    net_kg = max(0.0, gross_kg * (1.0 - crop_technique.loss_fraction)
                 - crop_technique.seed_kg_per_cropped_hectare * site.cropped_hectares)
    return [(parameter(world_map, "food_source_crops"), None, net_kg * crop_technique.kcal_per_kg)]
