"""How much of a resource a tile holds: known deposits plus the expected undiscovered ones.

Expected undiscovered deposits of a type in a tile =
    density_per_million_km2 / 1e6 * tile_area * permissiveness * clustering - known deposits of that type in the tile
Permissiveness is 0 to 1: the type's `permissive_when` conditions (all must hold), times its
`envelope` suitability, times each `layer_weights` entry ({"layer", "weights": {value: weight},
"default", "if_missing"}). Clustering is 1 + gain * sum(exp(-distance / length)) over known deposits
of the resource (a type with `"provincial_only": true` has gain * sum over known deposits of that
type alone, so it is zero where the catalogue has none nearby), capped. Sizes are lognormal,
truncated above, so the expected contained quantity per deposit is a closed form.
"""
import math
from typing import Any, Dict, List

from sim.geography import content_rules, parameters, resources_biotic, tile_layers
from sim.geography.distance import haversine_km
from sim.geography.map_source import MapDataError, WorldMap
from sim.geography.resources_catalogue import (BIOTIC_MECHANISM, grade_key, known_deposits, resource)
from sim.geography.resources_draws import truncated_lognormal_mean

SQUARE_KM_PER_MILLION = 1e6


def tile_of(world_map: WorldMap, tile_id: str) -> Dict[str, Any]:
    tile = world_map.tiles.get(tile_id)
    if tile is None:
        raise MapDataError("map %r has no tile %r" % (world_map.map_id, tile_id))
    return tile


def permissiveness(world_map: WorldMap, tile_id: str, deposit_type: Dict[str, Any]) -> float:
    """0 to 1: how well the tile's layers suit this deposit type."""
    lookup = tile_layers.reader(world_map, tile_id)
    if not content_rules.matches(deposit_type.get("permissive_when", []), lookup):
        return 0.0
    total = content_rules.suitability(deposit_type.get("envelope", []), lookup)
    for rule in deposit_type.get("layer_weights", []):
        found = lookup(rule["layer"])
        if found is None:
            total *= float(rule.get("if_missing", 0.0))
        else:
            total *= float(rule["weights"].get(str(found), rule.get("default", 0.0)))
    return total


def clustering_multiplier(world_map: WorldMap, tile_id: str, resource_id: str, deposit_type: Dict[str, Any]) -> float:
    """Density multiplier from known deposits nearby (metallogenic provinces)."""
    tile = tile_of(world_map, tile_id)
    length = parameters.parameter(world_map, "resources_cluster_length_km")
    gain = parameters.parameter(world_map, "resources_cluster_gain")
    cap = parameters.parameter(world_map, "resources_cluster_cap")
    provincial = bool(deposit_type.get("provincial_only"))
    total = 0.0
    for known in known_deposits(world_map, resource_id):
        if provincial and known["deposit_type"] != deposit_type["id"]:
            continue
        total += math.exp(-haversine_km(tile["lat"], tile["lon"], known["lat"], known["lon"]) / length)
    if deposit_type.get("clusters") is False:
        total = 0.0
    return min(cap, gain * total if provincial else 1.0 + gain * total)


def expected_counts(world_map: WorldMap, tile_id: str, resource_id: str) -> List[Dict[str, Any]]:
    """Per deposit type: expected number of undiscovered deposits in the tile (cached)."""
    cache = world_map.__dict__.setdefault("_resource_cache", {}).setdefault("counts", {})
    key = (tile_id, resource_id)
    if key not in cache:
        entry = resource(world_map, resource_id)
        area = float(tile_of(world_map, tile_id)["land_area_km2"])
        known_here = [known for known in known_deposits(world_map, resource_id) if known["tile_id"] == tile_id]
        rows = []
        for deposit_type in entry["deposit_types"]:
            density = deposit_type["deposits_per_million_km2"] / SQUARE_KM_PER_MILLION
            gross = (density * area * permissiveness(world_map, tile_id, deposit_type)
                     * clustering_multiplier(world_map, tile_id, resource_id, deposit_type))
            already = sum(1 for known in known_here if known["deposit_type"] == deposit_type["id"])
            rows.append({"deposit_type": deposit_type["id"], "expected_count": max(0.0, gross - already)})
        cache[key] = rows
    return cache[key]


def expected_contained_per_deposit(world_map: WorldMap, resource_entry: Dict[str, Any],
                                   deposit_type: Dict[str, Any]) -> float:
    """Mean contained quantity (resource unit) of one hidden deposit of the type."""
    limit = parameters.parameter(world_map, "resources_tonnage_truncation_sigmas")
    tonnage = deposit_type["tonnage_lognormal"]
    mean = truncated_lognormal_mean(tonnage["median_tonnes"], tonnage["sigma"], limit)
    if resource_entry.get("grade_basis"):
        grade = deposit_type["grade_lognormal"]
        mean *= truncated_lognormal_mean(grade[grade_key(resource_entry)], grade["sigma"], limit)
    return mean


def crustal_ceiling(world_map: WorldMap, tile_id: str, resource_entry: Dict[str, Any]) -> Any:
    """Most of an element that can be in ore in the tile (kg), or None when no abundance is given."""
    abundance_ppm = resource_entry.get("crustal_abundance_ppm")
    if abundance_ppm is None or resource_entry["unit"] != "kg":
        return None
    depth_m = parameters.parameter(world_map, "resources_crustal_depth_km") * 1000.0
    crust_mass_kg = (float(tile_of(world_map, tile_id)["land_area_km2"]) * 1e6 * depth_m
                     * parameters.parameter(world_map, "resources_crust_density_kg_per_m3"))
    return (abundance_ppm * 1e-6 * crust_mass_kg
            * parameters.parameter(world_map, "resources_ore_fraction_ceiling"))


def endowment(world_map: WorldMap, tile_id: str, resource_id: str) -> Dict[str, Any]:
    """{"unit", "known", "undiscovered_expected", "total", "expected_undiscovered_count", "ceiling"}.

    For a biotic stand the answer is resources_biotic.stand instead.
    """
    resource_entry = resource(world_map, resource_id)
    if resource_entry["mechanism"] == BIOTIC_MECHANISM:
        return resources_biotic.stand(world_map, tile_id, resource_id)
    types = {deposit_type["id"]: deposit_type for deposit_type in resource_entry["deposit_types"]}
    undiscovered, count = 0.0, 0.0
    for row in expected_counts(world_map, tile_id, resource_id):
        count += row["expected_count"]
        undiscovered += row["expected_count"] * expected_contained_per_deposit(
            world_map, resource_entry, types[row["deposit_type"]])
    ceiling = crustal_ceiling(world_map, tile_id, resource_entry)
    if ceiling is not None:
        undiscovered = min(undiscovered, ceiling)
    known = sum(deposit["quantity"] for deposit in known_deposits(world_map, resource_id)
                if deposit["tile_id"] == tile_id)
    return {"resource": resource_id, "unit": resource_entry["unit"], "known": known,
            "undiscovered_expected": undiscovered, "total": known + undiscovered,
            "expected_undiscovered_count": count, "ceiling": ceiling}
