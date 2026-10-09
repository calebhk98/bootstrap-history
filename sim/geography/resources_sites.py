"""The deposits a party can work: those it knows on the tiles it holds, sized in tonnes of the resource.

A catalogue deposit is known to a party that holds its tile once it was first worked (a deposit with no
working date is taken as known, a location the locals always knew); a deposit prospecting found
(`resources_prospecting.prospect`, kept by the caller) is known to whoever found it. Each row carries the
deposit's size in tonnes of the resource when the data gives one, and the grade of its ore, so a caller can
bound a working by the deposit: the most it can yield a year is a share of its size
(`resources_working_share_per_year`).

Standalone: the catalogue and parameters of this package.
"""
from typing import Any, Dict, Iterable, List, Mapping, Optional

from sim.geography import parameters, resources_catalogue
from sim.geography.map_source import WorldMap

TONNES_PER_UNIT = {"kg": 0.001, "tonnes": 1.0, "tonnes_oil_equivalent": 1.0}
KG_PER_TONNE = 1000.0


def size_in_tonnes(quantity: Optional[float], unit: str) -> Optional[float]:
    """A quantity in the resource's unit as tonnes, or None when the size or the unit has no mass."""
    factor = TONNES_PER_UNIT.get(unit)
    return None if quantity is None or factor is None else float(quantity) * factor


def worked_deposits(world_map: WorldMap, tile_ids: Iterable[str], resource_id: str, year: int,
                    found: Iterable[Mapping[str, Any]] = ()) -> List[Dict[str, Any]]:
    """Rows {id, name, tile_id, resource, size_tonnes (None: unknown), grade_kg_per_tonne (None: not an ore
    with a grade), found_by} of the deposits of `resource_id` a party holding `tile_ids` can name, with the
    prospected deposits (`found`, as `prospect` returns them) it has found; in id order."""
    tiles = set(tile_ids)
    rows = world_map.catalogue("deposits")
    resource_entry = resources_catalogue.resource(world_map, resource_id)
    unit = resource_entry["unit"]
    worked = []
    for deposit in resources_catalogue.known_deposits(world_map, resource_id):
        first_worked = rows[deposit["id"]].get("first_worked")
        if deposit["tile_id"] not in tiles or (first_worked is not None and first_worked > year):
            continue
        worked.append({"id": deposit["id"], "name": deposit["name"], "tile_id": deposit["tile_id"],
                       "resource": resource_id, "size_tonnes": size_in_tonnes(deposit["quantity"], unit),
                       "grade_kg_per_tonne": rows[deposit["id"]].get("ore_grade_kg_per_tonne"),
                       "found_by": "catalogue"})
    for deposit in found:
        if deposit["resource"] == resource_id and deposit["tile_id"] in tiles:
            worked.append({"id": deposit["id"], "name": deposit["id"], "tile_id": deposit["tile_id"],
                           "resource": resource_id, "size_tonnes": size_in_tonnes(deposit["contained"], unit),
                           "grade_kg_per_tonne": deposit.get("grade_per_tonne"), "found_by": "prospecting"})
    return sorted(worked, key=lambda row: row["id"])


def working_rate_tonnes_per_year(world_map: WorldMap, size_tonnes: float) -> float:
    """The most a deposit of this size yields a year: the share of it that can be worked."""
    return size_tonnes * float(parameters.parameter(world_map, "resources_working_share_per_year"))


def ore_tonnes_per_tonne(row: Mapping[str, Any]) -> float:
    """Tonnes of ore raised per tonne of the resource a deposit holds (1 for a resource that has no grade)."""
    grade = row.get("grade_kg_per_tonne")
    return KG_PER_TONNE / float(grade) if grade else 1.0
