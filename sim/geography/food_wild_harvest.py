"""Hunting draws the game stock down; each year the stock regrows.

`wild_stock` ({tile: {species: share of carrying capacity left}}, see food_wild_stock.py) is never changed in
place: each function returns a new one, with full stocks left out.
"""
from typing import Dict, Mapping, Optional

from sim.geography import content_rules
from sim.geography.food_productivity import (land_available_to_wild_km2, lookup, net_primary_production,
                                             rows_of_mechanism)
from sim.geography.food_wild import hunting_contributions, standing_stock_kg_per_km2
from sim.geography.food_wild_stock import regrown_fraction, stock_fraction
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter

FULL = 1.0 - 1e-9


def _without_full_stocks(wild_stock: Mapping) -> Dict[str, Dict[str, float]]:
    cleaned = {tile_id: {species_id: fraction for species_id, fraction in species.items() if fraction < FULL}
               for tile_id, species in wild_stock.items()}
    return {tile_id: species for tile_id, species in cleaned.items() if species}


def game_food_sources(world_map: WorldMap) -> list:
    """The food source ids that hunting wild animals goes under."""
    return sorted({row["food_source"] for row in rows_of_mechanism(world_map, "wild_population")})


def hunted_kcal_by_species(world_map: WorldMap, tile_id: str,
                           wild_stock: Optional[Mapping] = None) -> Dict[str, float]:
    """Energy a year's hunting can take from each species now, given the stock left."""
    return {species_id: kcal for _source, species_id, kcal in hunting_contributions(world_map, tile_id, wild_stock)}


def draw_down(world_map: WorldMap, wild_stock: Mapping, tile_id: str, kcal_taken: Mapping[str, float]) -> dict:
    """The stock after hunters take `kcal_taken` of each species on a tile."""
    reader = lookup(world_map, tile_id)
    productivity = net_primary_production(world_map, tile_id)
    area = land_available_to_wild_km2(world_map, tile_id)
    updated = {tile: dict(species) for tile, species in wild_stock.items()}
    for row in rows_of_mechanism(world_map, "wild_population"):
        taken = kcal_taken.get(row["id"], 0.0)
        fit = content_rules.suitability(row["envelope"], reader)
        capacity_kg = standing_stock_kg_per_km2(row, productivity, fit) * area
        if taken <= 0.0 or capacity_kg <= 0.0:
            continue
        killed_kg = taken / row["edible_kcal_per_kg_live"]
        left = max(0.0, stock_fraction(wild_stock, tile_id, row["id"]) - killed_kg / capacity_kg)
        updated.setdefault(tile_id, {})[row["id"]] = left
    return _without_full_stocks(updated)


def regrow(world_map: WorldMap, wild_stock: Mapping) -> dict:
    """The stock a year later: every drawn-down species regrows at its maximum rate by body size."""
    coefficient = parameter(world_map, "food_wild_growth_rate_coefficient")
    exponent = parameter(world_map, "food_wild_growth_rate_exponent")
    floor = parameter(world_map, "food_wild_recolonisation_fraction")
    rows = {row["id"]: row for row in rows_of_mechanism(world_map, "wild_population")}
    grown = {}
    for tile_id, species in wild_stock.items():
        grown[tile_id] = {
            species_id: regrown_fraction(fraction, coefficient * rows[species_id]["adult_mass_kg"] ** exponent, floor)
            for species_id, fraction in species.items() if species_id in rows}
    return _without_full_stocks(grown)
