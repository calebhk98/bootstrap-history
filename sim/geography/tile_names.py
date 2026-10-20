"""Readable facts about a land tile: its name, terrain and neighbours.

A tile has no historical place name in the data, so its name is its country
(from the tile record) and its number within that country. Nothing here is
specific to one actor.
"""
import functools
from typing import Any, Dict, List

from sim.geography import map_source
from sim.geography.loading import load_geography


def _tiles() -> Dict[str, Dict[str, Any]]:
    return map_source.load_map().tiles


def _climate_words(code: str) -> str:
    groups = map_source.load_map().catalogue("climate_groups")
    for length in range(len(code), 0, -1):
        if code[:length] in groups:
            return groups[code[:length]]["name"]
    return "unclassified"


@functools.lru_cache(maxsize=1)
def _region_names() -> Dict[str, str]:
    geography = load_geography()
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


def places_on(world_map: Any, tile_id: str) -> List[str]:
    """Names of the places the map's `places` catalogue (any overlay may add entries {id, name, tile, rank?}) puts on
    the tile, highest rank first; empty when the map has none."""
    found = [entry for entry in world_map.catalogue("places").values() if entry.get("tile") == tile_id]
    found.sort(key=lambda entry: (-entry.get("rank", 0), entry["name"]))
    return [entry["name"] for entry in found]


def region_name(tile_id: str) -> str:
    """The named region the tile lies in, or an empty string."""
    record = _tiles().get(tile_id) or {}
    return _region_names().get(record.get("old_region"), "")


def terrain(tile_id: str) -> str:
    """Climate in words, coast and the share of the ground that can be farmed."""
    record = _tiles().get(tile_id)
    if not record:
        return ""
    parts = [_climate_words(record.get("koppen_class", ""))]
    if record.get("coastal"):
        parts.append("coastal")
    parts.append("%d%% arable" % round(100 * record.get("arable_fraction", 0.0)))
    return ", ".join(parts)


def neighbours(tile_id: str) -> List[str]:
    return list((_tiles().get(tile_id) or {}).get("borders", []))
