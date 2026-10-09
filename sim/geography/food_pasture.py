"""Pastoral energy of a tile: grass production shared among the herd animals whose envelopes fit.

Grass production is the rain-limited herbaceous rate (capped by the tile's net production) on open,
unploughed, gentle land, cut by the growing season and by what wild grazers eat. Herds are charged
stored fodder for the months without growth. Herd animals split the usable forage in proportion to their
suitability; each head eats a fixed share of its body mass and returns milk and meat from its row.
"""
from typing import List, Mapping, Optional, Tuple

from sim.geography import content_rules, food_land, tile_layers
from sim.geography.food_productivity import (GRAMS_PER_KG, SQUARE_METRES_PER_SQUARE_KM, land_available_to_wild_km2,
                                             lookup, net_primary_production, rows_of_mechanism)
from sim.geography.food_season import growing_season_fraction
from sim.geography.food_wild import wild_grass_demand_g_per_m2
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR


def usable_forage_kg(world_map: WorldMap, tile_id: str, wild_stock: Optional[Mapping] = None) -> float:
    """Dry matter per year that grazing can take from the tile's open, unploughed land."""
    rain = tile_layers.number(world_map, tile_id, "annual_precipitation_mm", 0.0)
    grass = max(0.0, parameter(world_map, "food_pasture_forage_slope") * rain
                - parameter(world_map, "food_pasture_forage_offset"))
    grass = min(grass, net_primary_production(world_map, tile_id))
    # The rain formula is calibrated on a temperate season; a shorter one grows proportionally less.
    reference_season = parameter(world_map, "food_pasture_reference_season_fraction")
    grass *= min(1.0, growing_season_fraction(world_map, tile_id) / reference_season)
    grass = max(0.0, grass - wild_grass_demand_g_per_m2(world_map, tile_id, wild_stock))
    open_fraction = 1.0 - tile_layers.number(world_map, tile_id, "forest_fraction", 0.0)
    area = (land_available_to_wild_km2(world_map, tile_id) * open_fraction
            * food_land.grazable_fraction(world_map, tile_id))
    return (grass * SQUARE_METRES_PER_SQUARE_KM / GRAMS_PER_KG * area
            * parameter(world_map, "food_pasture_use_factor")
            * parameter(world_map, "food_pasture_digestibility_factor")
            * parameter(world_map, "food_pasture_mobility_factor"))


def kcal_per_head_year(row: dict) -> float:
    return (row["milk_litres_per_head_year"] * row["milk_kcal_per_litre"]
            + row["offtake_fraction_per_year"] * row["carcass_kg"] * row["carcass_kcal_per_kg"])


def herd_contributions(world_map: WorldMap, tile_id: str,
                       wild_stock: Optional[Mapping] = None) -> List[Tuple[str, str, float]]:
    reader = lookup(world_map, tile_id)
    suited = [(row, content_rules.suitability(row["envelope"], reader))
              for row in rows_of_mechanism(world_map, "herd_animal")]
    suited = [(row, fit) for row, fit in suited if fit > 0.0]
    if not suited:
        return []
    forage = usable_forage_kg(world_map, tile_id, wild_stock)
    crowding = max(1.0, sum(fit for _row, fit in suited))
    intake_fraction = parameter(world_map, "food_livestock_intake_fraction_per_day")
    # Months with no growth are fed from cut and stored fodder, which loses part of what was grown.
    season = growing_season_fraction(world_map, tile_id)
    fodder_charge = season + (1.0 - season) / parameter(world_map, "food_pasture_winter_fodder_efficiency")
    result = []
    for row, fit in suited:
        intake_per_head = row["adult_mass_kg"] * intake_fraction * CIVIL_DAYS_PER_YEAR * fodder_charge
        heads = forage * fit / crowding / intake_per_head
        result.append((row["food_source"], row["id"], heads * kcal_per_head_year(row)))
    return result
