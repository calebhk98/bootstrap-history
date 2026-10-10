"""How far a good travels: the reach its value pays for, and the span of a realm's own tiles.

A tonne is worth carrying only while carriage costs a small share of its value, so a good's market
reaches as far as that share of its value buys at the carriage rate. The economy's market areas and the
labour package's carriage need both read this one rule. Standalone: `sim.constants`, `distance` and the map.
"""
import itertools
import math
from typing import Iterable, Optional

from sim.constants import declare
from sim.geography import map_source
from sim.geography.distance import haversine_km

MARKET_AREA_THRESHOLD_SHARE = declare(
    "MARKET_AREA_THRESHOLD_SHARE", 0.15, kind="temporary_heuristic",
    unit="share of a good's value per tonne", source=None, confidence="D",
    why="Price gaps within a market are bounded by carriage; tiles whose carriage to the anchor is "
        "under this share of the value trade as one market. Not yet derived from trader margins "
        "and arbitrage speed.")

# Mean distance from the centre of a disc to a point in it, as a share of the radius.
MEAN_DISTANCE_IN_DISC = 2.0 / 3.0


def market_radius_km(value_per_tonne: float, carriage_cost_per_tonne_km: float) -> float:
    """Kilometres of carriage a tonne's value pays for before carriage passes the threshold share of it
    (both in one unit, such as labour-hours); unlimited when carriage is free."""
    if carriage_cost_per_tonne_km <= 0.0:
        return math.inf
    return MARKET_AREA_THRESHOLD_SHARE * max(0.0, value_per_tonne) / carriage_cost_per_tonne_km


def realm_span_km(tile_ids: Iterable[str], world_map=None) -> Optional[float]:
    """Mean great-circle distance between pairs of the given tiles, the distance between a realm's market
    areas; None for fewer than two tiles."""
    world_map = world_map if world_map is not None else map_source.load_map()
    points = []
    for tile_id in tile_ids:
        tile = world_map.tiles.get(tile_id)
        if tile is not None:
            points.append((tile["lat"], tile["lon"]))
    pairs = list(itertools.combinations(points, 2))
    if not pairs:
        return None
    return math.fsum(haversine_km(a[0], a[1], b[0], b[1]) for a, b in pairs) / len(pairs)
