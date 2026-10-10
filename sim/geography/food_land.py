"""Land a tile can plough or graze after slope and forest limits.

Arable land is the class arable share, held to the land not under forest except for the share
that can be cleared, then scaled by how gently the ground lies. Pasture has its own, looser slope
limit. Ruggedness is the measured mean elevation step between neighbouring raster cells.
"""
from sim.geography import content_rules, tile_layers
from sim.geography.map_source import WorldMap
from sim.geography.parameters import parameter


def _slope_factor(world_map: WorldMap, tile_id: str, envelope_parameter: str) -> float:
    return content_rules.suitability(parameter(world_map, envelope_parameter), tile_layers.reader(world_map, tile_id))


def arable_fraction(world_map: WorldMap, tile_id: str) -> float:
    """Share of the tile's land that can be ploughed."""
    forest = tile_layers.number(world_map, tile_id, "forest_fraction", 0.0)
    clearable = parameter(world_map, "food_forest_clearable_fraction")
    room = (1.0 - forest) + forest * clearable
    return min(tile_layers.number(world_map, tile_id, "arable_fraction", 0.0), room) \
        * _slope_factor(world_map, tile_id, "food_arable_ruggedness_envelope")


def cleared_forest_fraction(world_map: WorldMap, tile_id: str) -> float:
    """Share of the tile's land that is arable only because forest was cleared for it."""
    open_land = 1.0 - tile_layers.number(world_map, tile_id, "forest_fraction", 0.0)
    return max(0.0, arable_fraction(world_map, tile_id) - open_land)


def grazable_fraction(world_map: WorldMap, tile_id: str) -> float:
    """Share of open land that is gentle enough for livestock to use."""
    return _slope_factor(world_map, tile_id, "food_pasture_ruggedness_envelope")


HECTARES_PER_SQUARE_KM = 100.0


def arable_hectares(world_map: WorldMap, tile_id: str) -> float:
    """Hectares of the tile that can be ploughed."""
    return (tile_layers.number(world_map, tile_id, "land_area_km2", 0.0) * HECTARES_PER_SQUARE_KM
            * arable_fraction(world_map, tile_id))
