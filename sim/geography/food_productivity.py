"""Net primary production of a tile (Miami model with an aridity cap) and the helpers every food source shares.

Standalone: imports only the geography map modules.
"""
import math
from typing import Callable, List

from sim.geography import content_rules, food_land, mechanisms, tile_layers
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter

SQUARE_METRES_PER_SQUARE_KM = 1.0e6
GRAMS_PER_KG = 1000.0


def food_cache(world_map: WorldMap, name: str) -> dict:
    """A per-map scratch dictionary, so repeated food queries reuse earlier work."""
    return world_map.__dict__.setdefault("_food_cache", {}).setdefault(name, {})


def lookup(world_map: WorldMap, tile_id: str) -> Callable[[str], object]:
    return tile_layers.reader(world_map, tile_id)


def rows_of_mechanism(world_map: WorldMap, mechanism: str) -> List[dict]:
    """Every content row of the `resources` catalogue with this mechanism, in id order."""
    cache = food_cache(world_map, "rows")
    if mechanism not in cache:
        cache[mechanism] = [row for _row_id, row in sorted(mechanisms.rows_owned_by(world_map, "food").items())
                            if row.get("mechanism") == mechanism]
    return cache[mechanism]


def land_available_to_wild_km2(world_map: WorldMap, tile_id: str) -> float:
    """Land not under the plough: what wild animals and plants have."""
    area = tile_layers.number(world_map, tile_id, "land_area_km2", 0.0)
    return area * (1.0 - food_land.arable_fraction(world_map, tile_id))


def net_primary_production(world_map: WorldMap, tile_id: str) -> float:
    """Dry matter grown per m2 per year: Miami temperature and rain limits, an aridity cap, a thaw gate."""
    cache = food_cache(world_map, "npp")
    if tile_id in cache:
        return cache[tile_id]
    temperature = tile_layers.number(world_map, tile_id, "mean_temperature_c")
    rain = tile_layers.number(world_map, tile_id, "annual_precipitation_mm")
    result = 0.0
    if temperature is not None and rain is not None:
        ceiling = parameter(world_map, "food_npp_temperature_maximum")
        by_temperature = ceiling / (1.0 + math.exp(parameter(world_map, "food_npp_temperature_offset")
                                                   - parameter(world_map, "food_npp_temperature_slope") * temperature))
        by_rain = ceiling * (1.0 - math.exp(-parameter(world_map, "food_npp_precipitation_rate") * rain))
        by_aridity = parameter(world_map, "food_npp_dry_slope") * rain - parameter(world_map, "food_npp_dry_offset")
        thaw = content_rules.suitability(parameter(world_map, "food_npp_growing_warmth_envelope"),
                                         lookup(world_map, tile_id))
        result = max(0.0, min(by_temperature, by_rain, by_aridity)) * thaw
    cache[tile_id] = result
    return result


def net_primary_energy_per_km2(world_map: WorldMap, tile_id: str) -> float:
    """kcal of plant matter grown per km2 per year."""
    return (net_primary_production(world_map, tile_id) * SQUARE_METRES_PER_SQUARE_KM
            * parameter(world_map, "food_dry_matter_kcal_per_gram"))
