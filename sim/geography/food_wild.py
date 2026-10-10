"""Hunting and foraging energy of a tile, from the wild-animal and forage-plant rows of the map.

Hunting: standing biomass of a game guild is its row's biomass per unit of net primary production
times the tile's suitability, capped; the sustainable take is the stock times peak production
(Robinson and Redford) times the row's harvest fraction. Foraging: the edible share of net primary
production of each forage-plant row that fits the tile.
"""
import math
from typing import List, Mapping, Optional, Tuple

from sim.geography import content_rules
from sim.geography.food_productivity import (GRAMS_PER_KG, SQUARE_METRES_PER_SQUARE_KM, land_available_to_wild_km2,
                                             lookup, net_primary_energy_per_km2, net_primary_production,
                                             rows_of_mechanism)
from sim.geography.food_wild_stock import stock_fraction
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR


def standing_stock_kg_per_km2(row: dict, productivity: float, fit: float) -> float:
    return min(row["biomass_cap_kg_per_km2"], row["biomass_kg_per_km2_per_npp_g_m2"] * productivity * fit)


def wild_grass_demand_g_per_m2(world_map: WorldMap, tile_id: str, wild_stock: Optional[Mapping] = None) -> float:
    """Dry grass the tile's wild herbivores eat per m2 of land per year; herds share what is left.
    Hunted-down game eats less."""
    reader = lookup(world_map, tile_id)
    productivity = net_primary_production(world_map, tile_id)
    intake_per_kg_year = parameter(world_map, "food_livestock_intake_fraction_per_day") * CIVIL_DAYS_PER_YEAR
    demand_kg_per_km2 = 0.0
    for row in rows_of_mechanism(world_map, "wild_population"):
        fit = content_rules.suitability(row["envelope"], reader)
        if fit > 0.0:
            demand_kg_per_km2 += (standing_stock_kg_per_km2(row, productivity, fit)
                                  * stock_fraction(wild_stock, tile_id, row["id"])
                                  * row.get("grass_share_of_diet", 0.0) * intake_per_kg_year)
    return demand_kg_per_km2 * GRAMS_PER_KG / SQUARE_METRES_PER_SQUARE_KM


def hunting_contributions(world_map: WorldMap, tile_id: str,
                          wild_stock: Optional[Mapping] = None) -> List[Tuple[str, str, float]]:
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
        stock = standing_stock_kg_per_km2(row, productivity, fit)
        growth_rate = coefficient * row["adult_mass_kg"] ** exponent
        production = stock * peak * (math.exp(growth_rate) - 1.0)
        # Below the stock that gives peak production, surplus falls in proportion to the stock left.
        production *= min(1.0, stock_fraction(wild_stock, tile_id, row["id"]) / peak)
        kcal = production * row["harvest_fraction"] * row["edible_kcal_per_kg_live"] * area * accessibility
        result.append((row["food_source"], row["id"], kcal))
    return result


def foraging_contributions(world_map: WorldMap, tile_id: str, wild_stock: Optional[Mapping] = None) -> List[Tuple[str, str, float]]:
    reader = lookup(world_map, tile_id)
    plant_energy = net_primary_energy_per_km2(world_map, tile_id) * land_available_to_wild_km2(world_map, tile_id)
    return [(row["food_source"], row["id"],
             plant_energy * row["edible_fraction_of_npp"] * content_rules.suitability(row["envelope"], reader))
            for row in rows_of_mechanism(world_map, "forage_plant")]
