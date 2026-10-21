"""Arable share, fertility and heavy-soil share of a tile from the physical layers it has (Complaint 543).

Standalone like food_land: reads layers and parameters through the map. The water balance (rain against evaporation, from
sim/geography/soil_water_balance.py) and the growing months set the share of land that can bear a rainfed crop and how
much humus the soil holds; the ruggedness layer (read in food_land) limits slope. A large river's silt is not in the
fertility: it is the nitrogen input of flooded land (sim/geography/soil_nutrients.py). Texture has no layer, so the heavy
(clay) share is a stand-in from flat, wet ground until one exists.
"""
import math
from typing import Optional

from sim.geography import soil_water_balance, tile_layers
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter


def _ramp(value: float, low: float, high: float) -> float:
    """0 at or below `low`, 1 at or above `high`, straight between."""
    return 0.0 if value <= low else 1.0 if value >= high else (value - low) / (high - low)


def _climate(world_map: WorldMap, tile_id: str):
    names = ("mean_temperature_c", "coldest_month_temperature_c", "warmest_month_temperature_c", "annual_precipitation_mm", "lat")
    values = [tile_layers.number(world_map, tile_id, name) for name in names]
    return None if any(found is None for found in values) else values


def aridity_index(world_map: WorldMap, tile_id: str) -> Optional[float]:
    """Rain over Hargreaves evaporation for the tile; None when the tile has no climate layers or nothing evaporates."""
    climate = _climate(world_map, tile_id)
    if climate is None:
        return None
    mean_c, coldest_c, warmest_c, rain_mm, latitude = climate
    evaporation = soil_water_balance.evaporation_mm_per_year(
        latitude, mean_c, coldest_c, warmest_c, parameter(world_map, "soil_daily_temperature_range_c"))
    return soil_water_balance.aridity_index(rain_mm, evaporation)


def growing_season_adequacy(world_map: WorldMap, tile_id: str) -> float:
    """0 to 1: how far the tile's warm months run from too few to grow a cereal to enough for the full arable share."""
    climate = _climate(world_map, tile_id)
    if climate is None:
        return 0.0
    mean_c, coldest_c, warmest_c, _rain, _latitude = climate
    months = soil_water_balance.months_at_or_above(parameter(world_map, "food_grass_growth_threshold_c"), mean_c, coldest_c, warmest_c)
    return _ramp(months, parameter(world_map, "soil_least_growing_months"), parameter(world_map, "soil_full_arable_growing_months"))


def arable_fraction(world_map: WorldMap, tile_id: str) -> float:
    """Share of the tile's land a rainfed crop can bear: the ceiling for good ground, cut by dryness and a short season."""
    index = aridity_index(world_map, tile_id)
    if index is None:
        return 0.0
    moisture = _ramp(index, parameter(world_map, "soil_rainfed_floor_aridity_index"),
                     parameter(world_map, "soil_rainfed_full_aridity_index"))
    return parameter(world_map, "soil_arable_share_ceiling") * moisture * growing_season_adequacy(world_map, tile_id)


def fertility(world_map: WorldMap, tile_id: str) -> float:
    """Yield of the tile's arable ground against the reference field, from humus and leaching.
    Humus peaks where rain is near evaporation and falls off either way on a log scale; heat with rain beyond
    evaporation leaches a soil."""
    index = aridity_index(world_map, tile_id)
    floor = parameter(world_map, "soil_fertility_floor")
    if index is None or index <= 0.0:
        return floor
    spread = parameter(world_map, "soil_humus_spread")
    humus = math.exp(-(math.log(index / parameter(world_map, "soil_humus_optimum_aridity_index")) ** 2) / (2.0 * spread ** 2))
    mean_c = tile_layers.number(world_map, tile_id, "mean_temperature_c", 0.0)
    heat = _ramp(mean_c, parameter(world_map, "soil_leaching_onset_c"), parameter(world_map, "soil_leaching_full_c"))
    surplus = _ramp(index, parameter(world_map, "soil_leaching_onset_aridity_index"),
                    parameter(world_map, "soil_leaching_full_aridity_index"))
    leaching = 1.0 - parameter(world_map, "soil_leaching_loss") * heat * surplus
    cold_floor = parameter(world_map, "soil_cold_fertility_floor")
    season = growing_season_adequacy(world_map, tile_id)
    return max(floor, humus * leaching * (cold_floor + (1.0 - cold_floor) * season))


def heavy_soil_share(world_map: WorldMap, tile_id: str) -> float:
    """Share of the tile's arable ground that is heavy clay a light plough cannot open: flat, wet ground collects fine
    sediment and stays wet. Stand-in until a soil texture layer exists."""
    index = aridity_index(world_map, tile_id)
    if index is None:
        return 0.0
    rugged = tile_layers.number(world_map, tile_id, "ruggedness_index", 0.0)
    flat = 1.0 - _ramp(rugged, 0.0, parameter(world_map, "soil_heavy_ruggedness_limit"))
    wet = _ramp(index, parameter(world_map, "soil_heavy_onset_aridity_index"), parameter(world_map, "soil_heavy_full_aridity_index"))
    return parameter(world_map, "soil_heavy_share_ceiling") * flat * wet
