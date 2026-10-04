"""Sustainable food energy of a tile by source, and the people it supports.

    food_potential(world_map, tile_id, technique_factors=None)
        -> {"tile": id, "kcal_per_year": {source_id: kcal}, "total_kcal_per_year": kcal,
            "people_supported": number, "species": {group: [content ids with a nonzero yield]}}

`technique_factors` is a plain {source_id: multiplier} the caller supplies (what the actor's
techniques allow); a missing source counts 1. Source ids come from the content rows (and the
`food_source_crops` parameter), group names from the `food_species_group_of_mechanism` parameter.
Every source module returns (source_id, species_id, kcal) tuples; this module only adds them.
"""
from typing import Dict, Optional

from sim.geography.food_crops import crop_contributions
from sim.geography.food_fishing import fishing_contributions
from sim.geography.food_pasture import herd_contributions
from sim.geography.food_productivity import food_cache
from sim.geography.food_wild import foraging_contributions, hunting_contributions
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter

SOURCE_MODULES = (crop_contributions, herd_contributions, hunting_contributions, foraging_contributions,
                  fishing_contributions)


def _species_group(world_map: WorldMap, species_id: str) -> Optional[str]:
    mechanisms = parameter(world_map, "food_species_group_of_mechanism")
    row = world_map.catalogue("resources").get(species_id)
    return None if row is None else mechanisms.get(row.get("mechanism"))


def food_potential(world_map: WorldMap, tile_id: str,
                   technique_factors: Optional[Dict[str, float]] = None) -> dict:
    factors = technique_factors or {}
    kcal_by_source: Dict[str, float] = {}
    species: Dict[str, list] = {group: [] for group in parameter(world_map, "food_species_group_of_mechanism").values()}
    for source_module in SOURCE_MODULES:
        for source_id, species_id, kcal in source_module(world_map, tile_id):
            kcal = max(0.0, kcal) * factors.get(source_id, 1.0)
            kcal_by_source[source_id] = kcal_by_source.get(source_id, 0.0) + kcal
            group = None if species_id is None else _species_group(world_map, species_id)
            if kcal > 0.0 and group is not None:
                species[group].append(species_id)
    total = sum(kcal_by_source.values())
    return {"tile": tile_id, "kcal_per_year": kcal_by_source, "total_kcal_per_year": total,
            "people_supported": total / parameter(world_map, "food_kcal_per_person_year"),
            "species": {group: sorted(set(ids)) for group, ids in species.items()}}


def food_potential_all(world_map: WorldMap, technique_factors: Optional[Dict[str, float]] = None) -> Dict[str, dict]:
    """Every tile's food potential; cached per map and per set of technique factors."""
    cache = food_cache(world_map, "potential_all")
    key = tuple(sorted((technique_factors or {}).items()))
    if key not in cache:
        cache[key] = {tile_id: food_potential(world_map, tile_id, technique_factors)
                      for tile_id in world_map.tiles}
    return cache[key]
