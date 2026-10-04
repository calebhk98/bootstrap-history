"""Hunting and foraging energy of a tile, from the wild-animal and forage-plant rows of the map.

Hunting: standing biomass of a game guild is its row's biomass per unit of net primary production
times the tile's suitability, capped; the sustainable take is the stock times peak production
(Robinson and Redford) times the row's harvest fraction. Foraging: the edible share of net primary
production of each forage-plant row that fits the tile.
"""
import math
from typing import List, Tuple

from sim.geography import content_rules
from sim.geography.food_productivity import (land_available_to_wild_km2, lookup, net_primary_energy_per_km2,
                                             net_primary_production, rows_of_mechanism)
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter


def hunting_contributions(world_map: WorldMap, tile_id: str) -> List[Tuple[str, str, float]]:
    reader = lookup(world_map, tile_id)
    productivity = net_primary_production(world_map, tile_id)
    area = land_available_to_wild_km2(world_map, tile_id)
    coefficient = parameter(world_map, "food_wild_growth_rate_coefficient")
    exponent = parameter(world_map, "food_wild_growth_rate_exponent")
    peak = parameter(world_map, "food_wild_peak_production_stock_fraction")
    accessibility = parameter(world_map, "food_hunting_accessibility")
    result = []
    for row in rows_of_mechanism(world_map, "wild_population"):
        fit = content_rules.suitability(row["envelope"], reader)
        if fit <= 0.0:
            continue
        stock = min(row["biomass_cap_kg_per_km2"],
                    row["biomass_kg_per_km2_per_npp_g_m2"] * productivity * fit)
        growth_rate = coefficient * row["adult_mass_kg"] ** exponent
        production = stock * peak * (math.exp(growth_rate) - 1.0)
        kcal = production * row["harvest_fraction"] * row["edible_kcal_per_kg_live"] * area * accessibility
        result.append((row["food_source"], row["id"], kcal))
    return result


def foraging_contributions(world_map: WorldMap, tile_id: str) -> List[Tuple[str, str, float]]:
    reader = lookup(world_map, tile_id)
    plant_energy = net_primary_energy_per_km2(world_map, tile_id) * land_available_to_wild_km2(world_map, tile_id)
    return [(row["food_source"], row["id"],
             plant_energy * row["edible_fraction_of_npp"] * content_rules.suitability(row["envelope"], reader))
            for row in rows_of_mechanism(world_map, "forage_plant")]
