"""Model coefficients kept as map data, so a mod or another map can change them.

Each entry of the map's `parameters` catalogue is
{"id", "value", "unit", "kind", "source", "conf", "why"}; `kind` is "physical" (a constant of
nature or a measured material property), "measured" (an observed rate with a source), or
"heuristic" (a stand-in until the mechanism exists; these are the migration queue).
"""
from typing import Any, Dict, List

from sim.geography.map_source import MapDataError, WorldMap

KINDS = ("physical", "measured", "heuristic")


def parameter(world_map: WorldMap, parameter_id: str) -> Any:
    """The value of one parameter; a missing one is an error naming it."""
    entry = world_map.catalogue("parameters").get(parameter_id)
    if entry is None:
        raise MapDataError("map %r has no parameter %r (data/world/geography/parameters/)"
                           % (world_map.map_id, parameter_id))
    return entry["value"]


def heuristics(world_map: WorldMap) -> List[Dict[str, Any]]:
    """Every parameter still marked heuristic, for the burndown."""
    return [entry for _parameter_id, entry in sorted(world_map.catalogue("parameters").items())
            if entry.get("kind") == "heuristic"]


def invalid_entries(world_map: WorldMap) -> List[str]:
    """Ids of parameters missing a value, a known kind, a source or a reason."""
    return [parameter_id for parameter_id, entry in sorted(world_map.catalogue("parameters").items())
            if "value" not in entry or entry.get("kind") not in KINDS
            or not entry.get("source") or not entry.get("why")]
