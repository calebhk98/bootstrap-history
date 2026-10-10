"""Growing season of a tile from its annual temperature cycle: the share of the year warm enough for grass.

The yearly cycle is a sine wave through the tile's mean, as wide as its coldest and warmest months
say; the season is the part of the year above the growth threshold. A tile without the range layers
counts a whole year above the threshold when its mean is, and none when not.
"""
import math

from sim.geography import tile_layers
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter


def growing_season_fraction(world_map: WorldMap, tile_id: str) -> float:
    mean = tile_layers.number(world_map, tile_id, "mean_temperature_c")
    if mean is None:
        return 0.0
    threshold = parameter(world_map, "food_grass_growth_threshold_c")
    warmest = tile_layers.number(world_map, tile_id, "warmest_month_temperature_c")
    coldest = tile_layers.number(world_map, tile_id, "coldest_month_temperature_c")
    amplitude = 0.0 if warmest is None or coldest is None else max(0.0, (warmest - coldest) / 2.0)
    if amplitude <= 0.0:
        return 1.0 if mean > threshold else 0.0
    ratio = (threshold - mean) / amplitude
    if ratio <= -1.0:
        return 1.0
    if ratio >= 1.0:
        return 0.0
    return math.acos(ratio) / math.pi
