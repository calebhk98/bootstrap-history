"""A recorded census: how many people lived under each government, placed on the map tiles a country holds.

Pure. A census file lists entries with a seat (latitude, longitude) and a head count; each entry's people go to
the held tile nearest its seat. The distance function is handed in, so this module imports no geography."""
import json
import os
from typing import Any, Callable, Dict, List, Mapping, Tuple

CENSUS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                             "data", "world", "census")


def load_census(census_id: str) -> Dict[str, Any]:
    """The census file `data/world/census/<census_id>.json`."""
    with open(os.path.join(CENSUS_FOLDER, census_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


def place_on_nearest_tile(entries: List[Mapping[str, Any]], tiles: Mapping[str, Tuple[float, float]],
                          distance_km: Callable[[float, float, float, float], float]) -> Tuple[Dict[str, float], float]:
    """(people by tile, the farthest an entry's seat lay from the tile it was given): each entry's persons on
    the nearest tile (ties to the lower id). With no tiles nothing is placed."""
    placed: Dict[str, float] = {}
    farthest = 0.0
    if not tiles:
        return placed, farthest
    for entry in entries:
        gap, tile = min((distance_km(entry["seat_lat"], entry["seat_lon"], lat, lon), tile_id)
                        for tile_id, (lat, lon) in sorted(tiles.items()))
        placed[tile] = placed.get(tile, 0.0) + float(entry["persons"])
        farthest = max(farthest, gap)
    return dict(sorted(placed.items())), farthest
