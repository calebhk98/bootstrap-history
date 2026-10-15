"""What known deposits have yielded before a year, from their size and the year each was first worked.

A deposit is worked from `first_worked` and each year yields a fixed share of what it still holds, so its
yield falls as it empties and it is never worked out at a stroke after some horizon. The share is the
deposit's historical extraction rate over its size when the caller has that rate as data (`rates`, tonnes of
the resource a year), else `resources_working_share_per_year`. Deposits with no working date, first worked
after the year asked about, or of no known size have yielded nothing here and are named so the caller can
say what it could not derive.
"""
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional

from sim.geography import parameters, resources_catalogue, resources_district
from sim.geography.map_source import WorldMap
from sim.geography.resources_sites import TONNES_PER_UNIT


def mined_before(world_map: WorldMap, tile_ids: Iterable[str], resource_id: str, year: int,
                 rates: Optional[Mapping[str, float]] = None) -> Dict[str, Any]:
    """{workings, unworked, deposits_in_tiles, unit} for the known deposits of a resource in these tiles.

    A working is {id, tile_id, output_per_year, years_worked, years_since_last_output, mined_share}: the
    yield per year now (in the resource's unit), the years that yield stands for (the deposit's e-folding
    time, or fewer when it was first worked more recently), 0 years since the last output, and the share of
    the deposit already yielded. `unworked` lists deposits that cannot have yielded by `year` (no working
    date, not yet worked, or no known size)."""
    default_share = float(parameters.parameter(world_map, "resources_working_share_per_year"))
    rates = rates or {}
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
        quantity, _basis = resources_district.district_quantity(world_map, deposit)
        if first is None or first > year or not quantity:
            unworked.append(deposit["id"])
            continue
        share = default_share
        if deposit["id"] in rates and unit in TONNES_PER_UNIT:
            share = rates[deposit["id"]] / (quantity * TONNES_PER_UNIT[unit])
        elapsed = float(year - first)
        mined_share = 1.0 - math.exp(-share * elapsed)
        workings.append({"id": deposit["id"], "tile_id": deposit["tile_id"],
                         "output_per_year": quantity * share * (1.0 - mined_share),
                         "years_worked": min(elapsed, 1.0 / share), "years_since_last_output": 0.0,
                         "mined_share": mined_share})
    return {"workings": workings, "unworked": unworked, "deposits_in_tiles": in_tiles, "unit": unit}
