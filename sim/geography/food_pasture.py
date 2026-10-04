"""Pastoral energy of a tile: grass production shared among the herd animals whose envelopes fit.

Grass production is the rain-limited herbaceous rate (capped by the tile's net production) on open,
unploughed land. Herd animals split the usable forage in proportion to their suitability; each head
eats a fixed share of its body mass and returns milk and meat from its row.
"""
from typing import List, Tuple

from sim.geography import content_rules, tile_layers
from sim.geography.food_productivity import (SQUARE_METRES_PER_SQUARE_KM, land_available_to_wild_km2,
                                             lookup, net_primary_production, rows_of_mechanism)
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter

DAYS_PER_YEAR = 365.0
GRAMS_PER_KG = 1000.0


def usable_forage_kg(world_map: WorldMap, tile_id: str) -> float:
    """Dry matter per year that grazing can take from the tile's open, unploughed land."""
    rain = tile_layers.number(world_map, tile_id, "annual_precipitation_mm", 0.0)
    grass = max(0.0, parameter(world_map, "food_pasture_forage_slope") * rain
                - parameter(world_map, "food_pasture_forage_offset"))
    grass = min(grass, net_primary_production(world_map, tile_id))
    open_fraction = 1.0 - tile_layers.number(world_map, tile_id, "forest_fraction", 0.0)
    area = land_available_to_wild_km2(world_map, tile_id) * open_fraction
    return (grass * SQUARE_METRES_PER_SQUARE_KM / GRAMS_PER_KG * area
            * parameter(world_map, "food_pasture_use_factor")
            * parameter(world_map, "food_pasture_digestibility_factor")
            * parameter(world_map, "food_pasture_mobility_factor"))


def kcal_per_head_year(row: dict) -> float:
    return (row["milk_litres_per_head_year"] * row["milk_kcal_per_litre"]
            + row["offtake_fraction_per_year"] * row["carcass_kg"] * row["carcass_kcal_per_kg"])


def herd_contributions(world_map: WorldMap, tile_id: str) -> List[Tuple[str, str, float]]:
    reader = lookup(world_map, tile_id)
    suited = [(row, content_rules.suitability(row["envelope"], reader))
              for row in rows_of_mechanism(world_map, "herd_animal")]
    suited = [(row, fit) for row, fit in suited if fit > 0.0]
    if not suited:
        return []
    forage = usable_forage_kg(world_map, tile_id)
    crowding = max(1.0, sum(fit for _row, fit in suited))
    intake_fraction = parameter(world_map, "food_livestock_intake_fraction_per_day")
    result = []
    for row, fit in suited:
        intake_per_head = row["adult_mass_kg"] * intake_fraction * DAYS_PER_YEAR
        heads = forage * fit / crowding / intake_per_head
        result.append((row["food_source"], row["id"], heads * kcal_per_head_year(row)))
    return result
