"""Who owns each tile and how firmly: the owner map every actor's territory is read from.

The map is {tile id: {"owner": actor id}}; an actor is any country or seat. A tile has at most one entry, so it
has at most one owner. How firmly it is held is the tile store `control` (sim/engine/mod_stores.py), passed in as
`controls`; the levels are data (data/world/control_levels.json).
"""
import functools
import json
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from sim.geography import map_source

OwnerMap = Dict[str, Dict[str, str]]
LEVELS_FILE = os.path.join(map_source.ROOT, "data", "world", "control_levels.json")


class TileOwnerError(ValueError):
    """A transfer or seeding that would break the one-owner rule."""


@functools.lru_cache(maxsize=1)
def _data() -> Dict[str, Any]:
    with open(LEVELS_FILE, encoding="utf-8") as handle:
        return json.load(handle)


def control_levels() -> Dict[str, Dict[str, Any]]:
    """{level: {rank, description}} for every control level."""
    return {level: dict(entry) for level, entry in _data()["levels"].items()}


def seed_level() -> str:
    """The level a civilisation file's own tiles open at."""
    return str(_data()["seed_level"])


def settlement_level() -> str:
    """The level a newly founded colony's tile is held at."""
    return str(_data()["settlement_level"])


def conquest_level(years_held: Optional[float] = None) -> str:
    """The level a tile taken by an army is held at: `initial` when it has just been taken (`years_held` None or 0),
    and each step's level once the owner has held it with an army that many years (the highest step reached)."""
    conquest = _data()["conquest"]
    level = str(conquest["initial"])
    for step in sorted(conquest["steps"], key=lambda entry: entry["after_years"]):
        if years_held is not None and years_held >= step["after_years"]:
            level = str(step["level"])
    _require_level(level)
    return level


def seed(claims: Mapping[str, Iterable[str]], level: Optional[str] = None) -> Tuple[OwnerMap, List[Dict[str, Any]]]:
    """(owner map, conflicts) from {actor: tiles it claims}. Claimants are read in order; the first to claim
    a tile keeps it and each later claim of it is reported as {tile, owner, claimant}."""
    level = level or seed_level()
    _require_level(level)
    owners: OwnerMap = {}
    conflicts: List[Dict[str, Any]] = []
    for actor, tiles in claims.items():
        for tile_id in sorted(set(tiles)):
            held = owners.get(tile_id)
            if held is not None:
                conflicts.append({"tile": tile_id, "owner": held["owner"], "claimant": actor})
            else:
                owners[tile_id] = {"owner": actor}
    return owners, conflicts


def owner_of(owners: Mapping[str, Mapping[str, str]], tile_id: str) -> Optional[str]:
    entry = owners.get(tile_id)
    return entry["owner"] if entry else None


def control_of(controls: Any, tile_id: str) -> Optional[str]:
    """The control level the `control` tile store holds for a tile (None when unowned)."""
    return controls.get(tile_id)


def seed_controls(owners: Mapping[str, Any], controls: Any, level: Optional[str] = None) -> None:
    """Write the seed level to the `controls` store for every owned tile."""
    level = level or seed_level()
    _require_level(level)
    for tile_id in owners:
        controls.set(tile_id, level)


def tiles_of(owners: Mapping[str, Mapping[str, str]], actor: str) -> List[str]:
    """Sorted tiles this actor owns, at any control level."""
    return sorted(tile_id for tile_id, entry in owners.items() if entry["owner"] == actor)


def transfer(owners: OwnerMap, tile_id: str, to_actor: Optional[str], level: Optional[str] = None,
             world_map: Optional[map_source.WorldMap] = None, controls: Any = None) -> Optional[str]:
    """Give a tile (and its control level, written to the `controls` store) to an actor, or release it
    (`to_actor` None); returns the previous owner (None when unowned). The one operation that changes who owns a
    tile; refuses a tile the map lacks or an unlisted level."""
    level = level or seed_level()
    _require_level(level)
    if world_map is not None and tile_id not in world_map.tiles:
        raise TileOwnerError("no such tile: %s" % tile_id)
    previous = owner_of(owners, tile_id)
    if to_actor is None:
        owners.pop(tile_id, None)
    else:
        owners[tile_id] = {"owner": to_actor}
    if controls is not None:
        controls.set(tile_id, None if to_actor is None else level)
    return previous


def way_owner(owners: Mapping[str, Mapping[str, str]], key: str) -> Optional[str]:
    """The owner of a built way: a port's tile owner, or an edge's owner when both ends share one (None when the
    ends are held by different actors or unowned)."""
    ends = {owner_of(owners, tile_id) for tile_id in key.split("|")}
    return ends.pop() if len(ends) == 1 else None


def problems(owners: Mapping[str, Mapping[str, str]], claims: Optional[Mapping[str, Iterable[str]]] = None,
             world_map: Optional[map_source.WorldMap] = None, controls: Any = None) -> List[Dict[str, Any]]:
    """What breaks the one-owner rule, each {cause, tile, ...}: no owner, unknown control level, a tile the map
    lacks, and (given `claims`, each actor's own list of tiles) a tile two actors list (cause "double_claim") or
    one lists that the map gives another (cause "owned_by_other")."""
    found: List[Dict[str, Any]] = []
    levels = _data()["levels"]
    for tile_id, entry in sorted(owners.items()):
        if not entry.get("owner"):
            found.append({"cause": "no_owner", "tile": tile_id})
        if controls is not None and controls.get(tile_id) not in levels:
            found.append({"cause": "unknown_control", "tile": tile_id, "control": controls.get(tile_id)})
        if world_map is not None and tile_id not in world_map.tiles:
            found.append({"cause": "not_on_map", "tile": tile_id})
    listed: Dict[str, str] = {}
    for actor, tiles in (claims or {}).items():
        for tile_id in sorted(set(tiles)):
            if listed.get(tile_id, actor) != actor:
                found.append({"cause": "double_claim", "tile": tile_id, "actors": [listed[tile_id], actor]})
            listed.setdefault(tile_id, actor)
            if owner_of(owners, tile_id) not in (None, actor):
                found.append({"cause": "owned_by_other", "tile": tile_id, "claimant": actor,
                              "owner": owner_of(owners, tile_id)})
    return found


def _require_level(level: str) -> None:
    if level not in _data()["levels"]:
        raise TileOwnerError("unknown control level: %s" % level)
