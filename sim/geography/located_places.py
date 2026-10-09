"""The tiles a located material comes from.

A located material lists `places`. A place is a position (`lat` and `lon`) with the source that puts the
material there, or `{"deposit": id}` naming a catalogued deposit whose position it takes. Each resolves to
the tile holding it, like a deposit, so the material is reached through the tile and never a region label.
Standalone: data only.
"""
from typing import Any, Dict, List, Tuple

from sim.geography import tile_lookup


def tiles(material: Dict[str, Any], geography: Dict[str, Any], deposit_rows: List[Dict[str, Any]]) -> Tuple[str, ...]:
    """Sorted, deduplicated tile ids of a located material's places."""
    by_id = {row["id"]: row for row in deposit_rows}
    map_tiles = geography.get("land_tiles", {}).get("tiles", {})
    found = set()
    for place in material.get("places") or []:
        position = by_id[place["deposit"]] if "deposit" in place else place
        found.add(tile_lookup.nearest_tile_id(map_tiles, position["lat"], position["lon"]))
    found.discard(None)
    return tuple(sorted(found))
