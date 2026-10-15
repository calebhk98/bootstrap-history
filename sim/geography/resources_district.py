"""The size of a named district the catalogue gives no endowment for, from the geological model.

A district with a position but no endowment figure takes the expected contained quantity of one deposit of
its mineral: of the district's own `deposit_type` when the mineral defines that type, else the mean over the
mineral's types weighted by their deposit counts (`deposits_per_million_km2`). Each type's mean is the closed
form of its tonnage (and grade) lognormal truncated at `resources_tonnage_truncation_sigmas`, the same expected
size the endowment model gives a hidden deposit; the tile's crustal ceiling (its area, `resources_crustal_depth_km`,
`resources_crust_density_kg_per_m3`, `resources_ore_fraction_ceiling`) bounds it. No figure is stored per
district. A row carrying `share_of_empire_output` is sized by the older output model of the engine, so it
is left alone here.
"""
from typing import Any, Dict, Optional, Tuple

from sim.geography import resources_catalogue
from sim.geography.map_source import WorldMap
from sim.geography.resources_endowment import crustal_ceiling, expected_contained_per_deposit

CATALOGUE_BASIS = "catalogue"
TYPE_BASIS = "expected_for_deposit_type:%s"
MINERAL_BASIS = "expected_across_types_of:%s"
SIZING_PARAMETER = "resources_tonnage_truncation_sigmas"


def _expected_for_resource(world_map: WorldMap, resource_id: str, deposit_type_id: Optional[str]) -> Tuple[float, str]:
    """(expected contained quantity of one deposit, basis) for a mineral and a district type."""
    cache = world_map.__dict__.setdefault("_resource_cache", {}).setdefault("district", {})
    key = (resource_id, deposit_type_id)
    if key not in cache:
        entry = resources_catalogue.resource(world_map, resource_id)
        types = entry["deposit_types"]
        named = [deposit_type for deposit_type in types if deposit_type["id"] == deposit_type_id]
        if named:
            cache[key] = (expected_contained_per_deposit(world_map, entry, named[0]), TYPE_BASIS % deposit_type_id)
        else:
            weight = sum(deposit_type["deposits_per_million_km2"] for deposit_type in types)
            mean = sum(deposit_type["deposits_per_million_km2"] / weight
                       * expected_contained_per_deposit(world_map, entry, deposit_type) for deposit_type in types)
            cache[key] = (mean, MINERAL_BASIS % resource_id)
    return cache[key]


def district_quantity(world_map: WorldMap, deposit: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
    """(quantity in the resource's unit, basis) of a `known_deposits` row: the catalogue's endowment when it
    has one, else the geological model's expectation for the district. (None, None) for a row sized by the
    empire-output model."""
    if deposit["quantity"] is not None:
        return deposit["quantity"], CATALOGUE_BASIS
    if "share_of_empire_output" in world_map.catalogue("deposits")[deposit["id"]]:
        return None, None
    resource_id = deposit["resource"]
    quantity, basis = _expected_for_resource(world_map, resource_id, deposit.get("deposit_type"))
    ceiling = crustal_ceiling(world_map, deposit["tile_id"], resources_catalogue.resource(world_map, resource_id))
    if ceiling is not None:
        quantity = min(quantity, ceiling)
    return quantity, basis
