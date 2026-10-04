"""Resource definitions and the known-deposit catalogue of a map, loaded and validated.

A resource (map catalogue `resources`) is {"id", "mechanism", "unit", ...}:
  mineral_deposit, point_occurrence, surface_stock: "deposit_types" (see data/world/geography/resources/*.json),
      optional "grade_basis" (true: ore tonnes times grade is the contained quantity), "unit_factors"
      ({endowment_unit: multiplier into "unit"}), "crustal_abundance_ppm".
  biotic_stand: "envelope" and "stand" (see resources_biotic.py).
A known deposit (map catalogue `deposits`) is {"id", "resource", "lat", "lon", "endowment",
"endowment_unit", optional "deposit_type", "ore_grade_kg_per_tonne", "depth_class", "status"}. Known
deposits are not hidden: they sit in the tile nearest their coordinates.
"""
import math
from typing import Any, Dict, List

from sim.geography import mechanisms, parameters
from sim.geography.map_source import MapDataError, WorldMap

DEPOSIT_MECHANISMS = ("mineral_deposit", "point_occurrence", "surface_stock")
BIOTIC_MECHANISM = "biotic_stand"
FOLDER = "data/world/geography/resources/"


def _cache(world_map: WorldMap) -> Dict[Any, Any]:
    return world_map.__dict__.setdefault("_resource_cache", {})


def is_foreign(world_map: WorldMap, resource: Dict[str, Any]) -> bool:
    """True for entries another model owns (animals, wild plants): present in the catalogue, not ours."""
    return mechanisms.owner(resource.get("mechanism"), resource.get("id", "?")) != "resources"


def grade_key(resource: Dict[str, Any]) -> str:
    return "median_%s_per_tonne" % resource["unit"]


def _check_type(world_map: WorldMap, resource: Dict[str, Any], deposit_type: Dict[str, Any]) -> None:
    where = "resource %r deposit type %r (%s)" % (resource["id"], deposit_type.get("id"), FOLDER)
    for key in ("id", "deposits_per_million_km2", "tonnage_lognormal", "depth_class"):
        if key not in deposit_type:
            raise MapDataError("%s: missing %r" % (where, key))
    if "median_tonnes" not in deposit_type["tonnage_lognormal"] or "sigma" not in deposit_type["tonnage_lognormal"]:
        raise MapDataError("%s: tonnage_lognormal needs median_tonnes and sigma" % where)
    if resource.get("grade_basis"):
        grade = deposit_type.get("grade_lognormal", {})
        if grade_key(resource) not in grade or "sigma" not in grade:
            raise MapDataError("%s: grade_lognormal needs %s and sigma" % (where, grade_key(resource)))
    if deposit_type["depth_class"] not in parameters.parameter(world_map, "resources_visibility_by_depth_class"):
        raise MapDataError("%s: depth_class %r has no visibility in parameter resources_visibility_by_depth_class"
                           % (where, deposit_type["depth_class"]))


def resource_definitions(world_map: WorldMap) -> Dict[str, Dict[str, Any]]:
    """{resource_id: entry} of every resource this model handles, validated; others' entries are left out."""
    cache = _cache(world_map)
    if "definitions" in cache:
        return cache["definitions"]
    result = {}
    for resource_id, resource in sorted(world_map.catalogue("resources").items()):
        if is_foreign(world_map, resource):
            continue
        mechanism = resource.get("mechanism")
        if mechanism not in DEPOSIT_MECHANISMS + (BIOTIC_MECHANISM,):
            raise MapDataError("resource %r (%s): unknown mechanism %r; known: %s" % (
                resource_id, FOLDER, mechanism, ", ".join(DEPOSIT_MECHANISMS + (BIOTIC_MECHANISM,))))
        if "unit" not in resource:
            raise MapDataError("resource %r (%s): missing unit" % (resource_id, FOLDER))
        if mechanism == BIOTIC_MECHANISM:
            if "envelope" not in resource or "stand" not in resource:
                raise MapDataError("resource %r (%s): a biotic_stand needs envelope and stand" % (resource_id, FOLDER))
        else:
            if not resource.get("deposit_types"):
                raise MapDataError("resource %r (%s): needs deposit_types" % (resource_id, FOLDER))
            for deposit_type in resource["deposit_types"]:
                _check_type(world_map, resource, deposit_type)
        result[resource_id] = resource
    cache["definitions"] = result
    return result


def resource(world_map: WorldMap, resource_id: str) -> Dict[str, Any]:
    found = resource_definitions(world_map).get(resource_id)
    if found is None:
        raise MapDataError("map %r has no resource %r handled by the endowment model" % (world_map.map_id, resource_id))
    return found


def known_quantity(entry: Dict[str, Any], resource_entry: Dict[str, Any]) -> float:
    """A known deposit's endowment in the resource's own unit."""
    endowment_unit = entry["endowment_unit"]
    amount = float(entry["endowment"])
    if endowment_unit == resource_entry["unit"]:
        return amount
    if endowment_unit == "tonnes_ore":
        if not resource_entry.get("grade_basis"):
            return amount
        grade = entry.get("ore_grade_kg_per_tonne")
        if grade is None:
            for deposit_type in resource_entry["deposit_types"]:
                if deposit_type["id"] == entry.get("deposit_type"):
                    grade = deposit_type["grade_lognormal"][grade_key(resource_entry)]
        if grade is None:
            raise MapDataError("known deposit %r: tonnes_ore needs ore_grade_kg_per_tonne" % entry["id"])
        return amount * float(grade)
    factor = resource_entry.get("unit_factors", {}).get(endowment_unit)
    if factor is None:
        raise MapDataError("known deposit %r: endowment_unit %r is not %r and resource %r has no unit_factors for it"
                           % (entry["id"], endowment_unit, resource_entry["unit"], resource_entry["id"]))
    return amount * float(factor)


def _nearest_tile(world_map: WorldMap, lat: float, lon: float) -> str:
    best, best_distance = None, math.inf
    cosine = math.cos(math.radians(lat))
    for tile_id, tile in world_map.tiles.items():
        north = tile["lat"] - lat
        if north * north >= best_distance:
            continue
        east = ((tile["lon"] - lon + 180.0) % 360.0 - 180.0) * cosine
        distance = north * north + east * east
        if distance < best_distance:
            best, best_distance = tile_id, distance
    return best


def known_deposits(world_map: WorldMap, resource_id: str) -> List[Dict[str, Any]]:
    """Catalogue deposits of one resource as plain dicts with tile_id, quantity (resource unit), lat and lon."""
    cache = _cache(world_map).setdefault("known", {})
    if resource_id not in cache:
        resource_entry = resource(world_map, resource_id)
        rows = []
        for deposit_id, entry in sorted(world_map.catalogue("deposits").items()):
            if entry.get("resource") != resource_id:
                continue
            for key in ("lat", "lon", "endowment", "endowment_unit"):
                if key not in entry:
                    raise MapDataError("known deposit %r (data/world/geography/deposits/): missing %r" % (deposit_id, key))
            rows.append({"id": deposit_id, "name": entry.get("name", deposit_id), "resource": resource_id,
                         "deposit_type": entry.get("deposit_type"), "lat": entry["lat"], "lon": entry["lon"],
                         "tile_id": _nearest_tile(world_map, entry["lat"], entry["lon"]),
                         "quantity": known_quantity(entry, resource_entry), "unit": resource_entry["unit"],
                         "depth_class": entry.get("depth_class"), "status": entry.get("status", "modern")})
        cache[resource_id] = rows
    return cache[resource_id]


def validate(world_map: WorldMap) -> List[str]:
    """Problems with the resource definitions and the catalogue, as messages; empty when sound."""
    try:
        for resource_id in resource_definitions(world_map):
            known_deposits(world_map, resource_id)
        known_ids = set(resource_definitions(world_map)) | {
            entry_id for entry_id, entry in world_map.catalogue("resources").items() if is_foreign(world_map, entry)}
        return ["known deposit %r names unknown resource %r" % (deposit_id, entry.get("resource"))
                for deposit_id, entry in sorted(world_map.catalogue("deposits").items())
                if entry.get("resource") not in known_ids]
    except MapDataError as error:
        return [str(error)]
