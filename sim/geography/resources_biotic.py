"""Biotic stands (timber forest, fibre and dye plants): where they grow and how much stands there.

A biotic resource is {"mechanism": "biotic_stand", "unit", "envelope": [content_rules envelope],
"stand": {"cover_layer", "cover_fraction_at_full_suitability", "stock_per_hectare_at_full_suitability",
"regrowth_per_hectare_per_year_at_full_suitability"}}.
Suitability is the envelope's value for the tile. The stand's area is the tile's land area times the
cover layer when the tile has one, else times suitability and the stand's own cover fraction (default: the heuristic parameter
resources_stand_cover_when_forest_layer_missing). Stock and regrowth per hectare scale with suitability.
"""
from typing import Any, Dict

from sim.geography import content_rules, parameters, tile_layers
from sim.geography.map_source import MapDataError, WorldMap
from sim.geography.resources_catalogue import BIOTIC_MECHANISM, resource

HECTARES_PER_SQUARE_KM = 100.0


def _biotic(world_map: WorldMap, resource_id: str) -> Dict[str, Any]:
    entry = resource(world_map, resource_id)
    if entry["mechanism"] != BIOTIC_MECHANISM:
        raise MapDataError("resource %r is a %s, not a biotic_stand" % (resource_id, entry["mechanism"]))
    return entry


def supports(world_map: WorldMap, tile_id: str, resource_id: str) -> float:
    """0 to 1: how well the tile's climate and layers suit the stand."""
    entry = _biotic(world_map, resource_id)
    return content_rules.suitability(entry["envelope"], tile_layers.reader(world_map, tile_id))


def stand(world_map: WorldMap, tile_id: str, resource_id: str) -> Dict[str, Any]:
    """{"unit", "suitability", "stand_area_hectares", "standing_stock", "annual_regrowth"} for the tile."""
    entry = _biotic(world_map, resource_id)
    suitability = supports(world_map, tile_id, resource_id)
    model = entry["stand"]
    area_hectares = float(world_map.tiles[tile_id]["land_area_km2"]) * HECTARES_PER_SQUARE_KM
    cover = tile_layers.number(world_map, tile_id, model.get("cover_layer", ""))
    if cover is None:
        cover = suitability * model.get("cover_fraction_at_full_suitability", parameters.parameter(
            world_map, "resources_stand_cover_when_forest_layer_missing"))
    stand_hectares = area_hectares * cover
    return {"resource": resource_id, "unit": entry["unit"], "suitability": suitability,
            "stand_area_hectares": stand_hectares,
            "standing_stock": stand_hectares * suitability * model["stock_per_hectare_at_full_suitability"],
            "annual_regrowth": stand_hectares * suitability
            * model["regrowth_per_hectare_per_year_at_full_suitability"]}
