"""Undiscovered deposits of a tile and what prospecting effort finds of them.

`hidden_deposits` is a pure function of (map, tile, resource, seed): the number of deposits of each
type is overdispersed around the tile's expected count, and every deposit's size, grade and
position come from sha256 draws (resources_draws.py). `prospect` keeps the deposits whose own fixed
discovery draw falls below the discovery probability at the given effort, so more effort always
finds a superset of what less effort found. Discovery probability per deposit is
1 - exp(-effort * visibility * (tonnes / reference_tonnes) ** size_exponent / effort_per_efold):
bigger and shallower deposits are found first.
"""
import math
from typing import Any, Dict, List

from sim.geography import parameters
from sim.geography.map_source import WorldMap
from sim.geography.resources_catalogue import BIOTIC_MECHANISM, grade_key, resource
from sim.geography.resources_draws import overdispersed_count, position_in_tile, truncated_lognormal, uniform
from sim.geography.resources_endowment import expected_counts, tile_of


def _draw_deposit(world_map: WorldMap, resource_entry: Dict[str, Any], deposit_type: Dict[str, Any],
                  tile_id: str, seed: Any, index: int) -> Dict[str, Any]:
    labels = (world_map.map_id, seed, tile_id, resource_entry["id"], deposit_type["id"], index)
    limit = parameters.parameter(world_map, "resources_tonnage_truncation_sigmas")
    tonnage = deposit_type["tonnage_lognormal"]
    tonnes = truncated_lognormal(tonnage["median_tonnes"], tonnage["sigma"], limit, *labels, "tonnage")
    tile = tile_of(world_map, tile_id)
    lat, lon = position_in_tile(tile["lat"], tile["lon"], float(tile["land_area_km2"]), *labels)
    deposit = {"id": "%s:%s:%s:%s:%d" % (tile_id, resource_entry["id"], deposit_type["id"], seed, index),
               "resource": resource_entry["id"], "deposit_type": deposit_type["id"], "tile_id": tile_id,
               "lat": lat, "lon": lon, "ore_tonnes": tonnes, "depth_class": deposit_type["depth_class"],
               "small_scale": bool(deposit_type.get("small_scale", False)), "unit": resource_entry["unit"],
               "status": "undiscovered"}
    if resource_entry.get("grade_basis"):
        grade = deposit_type["grade_lognormal"]
        deposit["grade_per_tonne"] = truncated_lognormal(grade[grade_key(resource_entry)], grade["sigma"], limit,
                                                         *labels, "grade")
        deposit["contained"] = tonnes * deposit["grade_per_tonne"]
    else:
        deposit["contained"] = tonnes
    fraction = deposit_type.get("gem_fraction")
    if fraction:
        deposit["gem_fraction"] = min(1.0, truncated_lognormal(fraction["median"], fraction["sigma"], limit,
                                                               *labels, "gem"))
    deposit["find_draw"] = uniform(*labels, "find")
    return deposit


def hidden_deposits(world_map: WorldMap, tile_id: str, resource_id: str, seed: Any) -> List[Dict[str, Any]]:
    """Every undiscovered deposit of the resource in the tile, as plain dicts (a biotic stand has none)."""
    resource_entry = resource(world_map, resource_id)
    if resource_entry["mechanism"] == BIOTIC_MECHANISM:
        return []
    dispersion = parameters.parameter(world_map, "resources_count_dispersion")
    types = {deposit_type["id"]: deposit_type for deposit_type in resource_entry["deposit_types"]}
    deposits = []
    for row in expected_counts(world_map, tile_id, resource_id):
        deposit_type = types[row["deposit_type"]]
        count = overdispersed_count(row["expected_count"], dispersion, world_map.map_id, seed, tile_id,
                                    resource_id, deposit_type["id"])
        deposits.extend(_draw_deposit(world_map, resource_entry, deposit_type, tile_id, seed, index)
                        for index in range(count))
    return deposits


def discovery_probability(world_map: WorldMap, deposit: Dict[str, Any], effort: float) -> float:
    """Chance that `effort` person-days of prospecting in the tile finds this deposit."""
    visibility = parameters.parameter(world_map, "resources_visibility_by_depth_class")[deposit["depth_class"]]
    size_factor = (deposit["ore_tonnes"] / parameters.parameter(world_map, "resources_discovery_reference_tonnes")
                   ) ** parameters.parameter(world_map, "resources_discovery_size_exponent")
    scale = parameters.parameter(world_map, "resources_discovery_effort_person_days_per_efold")
    return 1.0 - math.exp(-max(effort, 0.0) * visibility * size_factor / scale)


def prospect(world_map: WorldMap, tile_id: str, resource_id: str, effort: float, seed: Any) -> List[Dict[str, Any]]:
    """The hidden deposits found by `effort` person-days of prospecting; deterministic and monotone in effort."""
    found = []
    for deposit in hidden_deposits(world_map, tile_id, resource_id, seed):
        probability = discovery_probability(world_map, deposit, effort)
        if deposit["find_draw"] < probability:
            found.append(dict(deposit, status="found", discovery_probability=probability))
    return found
