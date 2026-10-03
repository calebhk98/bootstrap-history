"""Readable facts about a land tile: its name, terrain and neighbours.

A tile has no historical place name in the data, so its name is its country
(from the tile record) and its number within that country. Nothing here is
specific to one actor.
"""
import functools
from typing import Any, Dict, List

from sim.world import land

_CLIMATE_GROUPS = {
    "A": "tropical", "B": "dry", "C": "temperate", "D": "cold continental",
    "E": "polar",
}
_DRY_KINDS = {"W": "desert", "S": "steppe"}


@functools.lru_cache(maxsize=1)
def _tiles() -> Dict[str, Dict[str, Any]]:
    geography = land._load_json(land.GEOGRAPHY_FILE)
    return geography.get("land_tiles", {}).get("tiles", {})


@functools.lru_cache(maxsize=1)
def _region_names() -> Dict[str, str]:
    geography = land._load_json(land.GEOGRAPHY_FILE)
    return {region_id: record.get("name", region_id)
            for region_id, record in geography.get("regions", {}).items()
            if isinstance(record, dict)}


def region_names() -> Dict[str, str]:
    """Each region's display name, by region id."""
    return _region_names()


def tile_name(tile_id: str) -> str:
    """'<Country> <number>', e.g. 'China 10'; the id itself for an unknown tile."""
    record = _tiles().get(tile_id)
    if not record:
        return tile_id
    number = tile_id.rsplit("_", 1)[-1].lstrip("0") or "0"
    return "%s %s" % (record.get("country_majority", tile_id), number)


def region_name(tile_id: str) -> str:
    """The named region the tile lies in, or an empty string."""
    record = _tiles().get(tile_id) or {}
    return _region_names().get(record.get("old_region"), "")


def terrain(tile_id: str) -> str:
    """Climate in words, coast and the share of the ground that can be farmed."""
    record = _tiles().get(tile_id)
    if not record:
        return ""
    code = record.get("koppen_class", "")
    climate = _CLIMATE_GROUPS.get(code[:1], "unclassified")
    if code[:1] == "B" and code[1:2] in _DRY_KINDS:
        climate = "dry %s" % _DRY_KINDS[code[1:2]]
    parts = [climate]
    if record.get("coastal"):
        parts.append("coastal")
    parts.append("%d%% arable" % round(100 * record.get("arable_fraction", 0.0)))
    return ", ".join(parts)


def neighbours(tile_id: str) -> List[str]:
    return list((_tiles().get(tile_id) or {}).get("borders", []))
