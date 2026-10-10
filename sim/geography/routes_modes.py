"""Carriage modes as map data: which edge classes a mode uses, what unlocks it, what it needs built.

A mode is an entry of the map's `route_modes` catalogue (see data/world/geography/route_modes/);
physics per mode is in `routes_rates.py`. Sea lanes (the `sea_lanes` catalogue) restrict open-sea
legs inside a lat/lon box to parties holding named tech nodes.

Standalone: reads the map, imports nothing outside this package.
"""
from typing import Any, Dict, FrozenSet, Iterable, List

from sim.geography.map_source import MapDataError, WorldMap

EDGE_CLASSES = ("land", "river", "coast", "open_sea")


def modes(world_map: WorldMap) -> Dict[str, Dict[str, Any]]:
    """{mode_id: mode entry} of the map."""
    return world_map.catalogue("route_modes")


def checked_mode_ids(world_map: WorldMap, mode_ids: Iterable[str]) -> FrozenSet[str]:
    """`mode_ids` as a set, each one a mode of the map."""
    known = modes(world_map)
    chosen = frozenset(mode_ids)
    unknown = sorted(chosen - set(known))
    if unknown:
        raise MapDataError("map %r has no route mode %s" % (world_map.map_id, ", ".join(unknown)))
    return chosen


CARGO_CLASSES = ("goods", "living_stock")


def carries(mode: Dict[str, Any], cargo: str) -> bool:
    """Whether a mode takes this class of cargo (a mode that names none takes every class)."""
    return cargo in (mode.get("carries") or CARGO_CLASSES)


def usable_modes(world_map: WorldMap, known_nodes_per_party: Iterable[Iterable[str]],
                 cargo: str = "goods") -> FrozenSet[str]:
    """Modes that carry `cargo` and whose required nodes every party holds (a mode with no requirement is
    always usable)."""
    parties = [frozenset(nodes) for nodes in known_nodes_per_party]
    return frozenset(mode_id for mode_id, mode in modes(world_map).items()
                     if carries(mode, cargo)
                     and all(frozenset(mode.get("requires_nodes") or ()) <= held for held in parties))


def walking_cargo_modes(world_map: WorldMap) -> FrozenSet[str]:
    """Modes where the cargo is the carrier (a herd driven to market)."""
    return frozenset(mode_id for mode_id, mode in modes(world_map).items() if mode.get("cargo_walks"))


def cargo_loss_per_day(world_map: WorldMap) -> Dict[str, float]:
    """{mode_id: share of the cargo lost each day on the road} for the modes that state one."""
    return {mode_id: float(mode["cargo_loss_per_day"]) for mode_id, mode in sorted(modes(world_map).items())
            if mode.get("cargo_loss_per_day")}


def improvement_nodes(world_map: WorldMap) -> Dict[str, str]:
    """{improvement key: tech node that lets an actor build it}, for the callers who build ways."""
    return {mode["needs_improvement"]: mode["improvement_node"] for mode in modes(world_map).values()
            if mode.get("needs_improvement") and mode.get("improvement_node")}


def sea_lanes(world_map: WorldMap) -> List[Dict[str, Any]]:
    """The sea lane rules, in id order."""
    return [entry for _lane_id, entry in sorted(world_map.catalogue("sea_lanes").items())]


def lane_requirements(world_map: WorldMap, latitude: float, longitude: float,
                      edge_class: str = "open_sea") -> FrozenSet[str]:
    """Tech nodes a sea leg of this class through this point needs, from every lane box that holds it."""
    needed = set()
    for lane in sea_lanes(world_map):
        box = lane["box"]
        if (edge_class in lane.get("edge_classes", ["open_sea"]) and box["lat_min"] <= latitude <= box["lat_max"]
                and box["lon_min"] <= longitude <= box["lon_max"]):
            needed.update(lane.get("requires_nodes") or ())
    return frozenset(needed)


def invalid_entries(world_map: WorldMap) -> List[str]:
    """Ids of modes missing a model, a known edge class, a source or a reason."""
    return [mode_id for mode_id, mode in sorted(modes(world_map).items())
            if not mode.get("model") or not mode.get("edge_classes")
            or any(edge_class not in EDGE_CLASSES for edge_class in mode["edge_classes"])
            or not mode.get("source") or not mode.get("why")
            or any(cargo not in CARGO_CLASSES for cargo in mode.get("carries") or ())]
