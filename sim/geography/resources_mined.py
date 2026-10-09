"""What known deposits have yielded before a year, from their endowment and the year each was first worked.

A deposit is worked from `first_worked` at a fixed share of its endowment a year until it is worked
out. Deposits with no working date, or first worked after the year asked about, have yielded nothing
here and are named so the caller can say what it could not derive.
"""
from typing import Any, Dict, Iterable, List

from sim.geography import parameters, resources_catalogue
from sim.geography.map_source import WorldMap


def mined_before(world_map: WorldMap, tile_ids: Iterable[str], resource_id: str, year: int) -> Dict[str, Any]:
    """{workings, unworked, deposits_in_tiles, unit} for the known deposits of a resource in these tiles.

    A working is {id, tile_id, output_per_year, years_worked, years_since_last_output}, output in the
    resource's unit; `unworked` lists deposits that cannot have yielded by `year` (no working date,
    not yet worked, or no known size)."""
    share = float(parameters.parameter(world_map, "resources_working_share_per_year"))
    tiles = set(tile_ids)
    rows = world_map.catalogue("deposits")
    workings: List[Dict[str, Any]] = []
    unworked: List[str] = []
    in_tiles = 0
    unit = resources_catalogue.resource(world_map, resource_id)["unit"]
    for deposit in resources_catalogue.known_deposits(world_map, resource_id):
        if deposit["tile_id"] not in tiles:
            continue
        in_tiles += 1
        first = rows[deposit["id"]].get("first_worked")
        if first is None or first > year or not deposit["quantity"]:
            unworked.append(deposit["id"])
            continue
        years_to_work_out = 1.0 / share
        years_worked = min(float(year - first), years_to_work_out)
        workings.append({"id": deposit["id"], "tile_id": deposit["tile_id"],
                         "output_per_year": deposit["quantity"] * share, "years_worked": years_worked,
                         "years_since_last_output": float(year - first) - years_worked})
    return {"workings": workings, "unworked": unworked, "deposits_in_tiles": in_tiles, "unit": unit}
