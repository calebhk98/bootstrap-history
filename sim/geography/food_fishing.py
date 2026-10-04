"""Fishing energy of a tile: marine shelf production by trophic level, and lake and river yields.

A fishery row names the layer that gives its extent (shelf area, lake area, river length). Marine
rows (with a trophic level) take a share of the shelf's primary production up the food chain
(Pauly and Christensen); other rows give a sustainable yield per unit of extent. A row may name a
parameter used as the extent when the layer has no value, only on tiles with a given field set.
"""
from typing import List, Optional, Tuple

from sim.geography import content_rules, tile_layers
from sim.geography.food_productivity import lookup, rows_of_mechanism
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter


def _extent(world_map: WorldMap, tile_id: str, row: dict) -> float:
    required = row.get("extent_requires_tile_field")
    if required is not None and not tile_layers.value(world_map, tile_id, required):
        return 0.0
    found: Optional[float] = tile_layers.number(world_map, tile_id, row["extent_layer"])
    if found is not None:
        return found
    if "extent_fallback_parameter" in row:
        return float(parameter(world_map, row["extent_fallback_parameter"]))
    return 0.0


def _marine_tonnes(world_map: WorldMap, tile_id: str, row: dict, extent_km2: float) -> float:
    production = tile_layers.number(world_map, tile_id, row["productivity_layer"])
    if not production:
        production = float(parameter(world_map, row["productivity_fallback_parameter"]))
    wet_per_carbon = parameter(world_map, "food_fish_wet_mass_per_gram_carbon")
    transfer = parameter(world_map, "food_fish_trophic_transfer_efficiency")
    tonnes_per_km2 = production * wet_per_carbon * transfer ** (row["trophic_level"] - 1.0)
    return (extent_km2 * tonnes_per_km2 * row["production_share"] * row["harvest_fraction"]
            * parameter(world_map, row["access_parameter"]))


def fishing_contributions(world_map: WorldMap, tile_id: str) -> List[Tuple[str, str, float]]:
    reader = lookup(world_map, tile_id)
    result = []
    for row in rows_of_mechanism(world_map, "fishery"):
        extent = _extent(world_map, tile_id, row)
        fit = content_rules.suitability(row["envelope"], reader)
        if extent <= 0.0 or fit <= 0.0:
            continue
        if "trophic_level" in row:
            tonnes = _marine_tonnes(world_map, tile_id, row, extent)
        else:
            tonnes = extent * row["yield_tonnes_per_unit"]
        result.append((row["food_source"], row["id"], tonnes * fit * row["edible_kcal_per_tonne"]))
    return result
