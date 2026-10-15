"""The size of a named district the catalogue gives no endowment for, from the geological model.

A district with a position but no endowment figure takes the expected contained quantity of one deposit of
its mineral: of the district's own `deposit_type` when the mineral defines that type, else the mean over the
mineral's types weighted by their deposit counts (`deposits_per_million_km2`). Each type's mean is the closed
form of its tonnage (and grade) lognormal truncated at `resources_tonnage_truncation_sigmas`, the same expected
size the endowment model gives a hidden deposit; the tile's crustal ceiling (its area, `resources_crustal_depth_km`,
`resources_crust_density_kg_per_m3`, `resources_ore_fraction_ceiling`) bounds it. No figure is stored per
district. A row carrying `share_of_empire_output` is sized by the older output model of the engine, so it
is left alone here. A district stating no ore grade takes the expected grade of the same draw, so the ore a
tonne of the resource takes to raise is not counted as pure metal.
"""
from typing import Any, Dict, Optional, Tuple

from sim.geography import resources_catalogue
from sim.geography.map_source import WorldMap
from sim.geography.resources_endowment import crustal_ceiling, expected_contained_per_deposit, expected_ore_grade

CATALOGUE_BASIS = "catalogue"
TYPE_BASIS = "expected_for_deposit_type:%s"
MINERAL_BASIS = "expected_across_types_of:%s"
SIZING_PARAMETER = "resources_tonnage_truncation_sigmas"


def _type_shares(entry: Dict[str, Any], deposit_type_id: Optional[str]):
    """([(deposit type, share of the deposits)], basis) a district of this type is drawn from: its own type
    when the mineral defines it, else all the mineral's types by their counts."""
    types = entry["deposit_types"]
    named = [deposit_type for deposit_type in types if deposit_type["id"] == deposit_type_id]
    if named:
        return [(named[0], 1.0)], TYPE_BASIS % deposit_type_id
    weight = sum(deposit_type["deposits_per_million_km2"] for deposit_type in types)
    return ([(deposit_type, deposit_type["deposits_per_million_km2"] / weight) for deposit_type in types],
            MINERAL_BASIS % entry["id"])


def _expected_for_resource(world_map: WorldMap, resource_id: str, deposit_type_id: Optional[str]) -> Tuple[float, str]:
    """(expected contained quantity of one deposit, basis) for a mineral and a district type."""
    cache = world_map.__dict__.setdefault("_resource_cache", {}).setdefault("district", {})
    key = (resource_id, deposit_type_id)
    if key not in cache:
        entry = resources_catalogue.resource(world_map, resource_id)
        shares, basis = _type_shares(entry, deposit_type_id)
        cache[key] = (sum(share * expected_contained_per_deposit(world_map, entry, deposit_type)
                          for deposit_type, share in shares), basis)
    return cache[key]


def district_grade(world_map: WorldMap, deposit: Dict[str, Any]) -> Optional[float]:
    """Grade (the resource's unit per tonne of ore) of a `known_deposits` row: the catalogue's when it states
    one, else the geological model's expectation for the district; None for a resource not mined as ore by
    grade."""
    stated = world_map.catalogue("deposits")[deposit["id"]].get("ore_grade_kg_per_tonne")
    entry = resources_catalogue.resource(world_map, deposit["resource"])
    if stated is not None or not entry.get("grade_basis") or entry["unit"] != "kg":
        return stated
    shares, _basis = _type_shares(entry, deposit.get("deposit_type"))
    return expected_ore_grade(world_map, entry, shares)


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
