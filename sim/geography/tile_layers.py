"""Per-tile values by name: a measured layer, else a field of the tile itself, else a derived rule.

Derived rules live in the map's `derived_layers` catalogue, so a map with only climate classes
(a fantasy map, or a tile a measured layer has no value for) still answers every query:

    {"id": "biome", "rule": "lookup", "key_layer": "koppen_class", "catalogue": "climate_classes",
     "field": "biome"}
    {"id": "koppen_group", "rule": "prefix", "source_layer": "koppen_class", "length": 1}
"""
from typing import Any, Callable, Dict, Optional

from sim.geography.map_source import MapDataError, WorldMap

_MISSING = object()


def _derive(world_map: WorldMap, tile_id: str, rule: Dict[str, Any], seen: frozenset) -> Any:
    kind = rule.get("rule")
    if kind == "lookup":
        key = value(world_map, tile_id, rule["key_layer"], seen)
        row = world_map.catalogue(rule["catalogue"]).get(str(key)) if key is not None else None
        return None if row is None else row.get(rule["field"])
    if kind == "prefix":
        source = value(world_map, tile_id, rule["source_layer"], seen)
        return None if source is None else str(source)[:int(rule["length"])]
    raise MapDataError("derived layer %r: unknown rule %r" % (rule.get("id"), kind))


def value(world_map: WorldMap, tile_id: str, name: str, seen: frozenset = frozenset()) -> Any:
    """The tile's value of `name`, or None when no layer, field or rule gives one."""
    cache = world_map.__dict__.setdefault("_layer_cache", {})
    key = (tile_id, name)
    cached = cache.get(key, _MISSING)
    if cached is not _MISSING:
        return cached
    if name in seen:
        raise MapDataError("derived layer %r depends on itself" % name)
    result = None
    layer = world_map.layers.get(name)
    if layer is not None:
        result = layer["values"].get(tile_id)
    if result is None:
        result = world_map.tiles.get(tile_id, {}).get(name)
    if result is None:
        rule = world_map.catalogue("derived_layers").get(name)
        if rule is not None:
            result = _derive(world_map, tile_id, rule, seen | {name})
    cache[key] = result
    return result


def number(world_map: WorldMap, tile_id: str, name: str, default: Optional[float] = None) -> Optional[float]:
    """The tile's value of `name` as a float, or `default`."""
    found = value(world_map, tile_id, name)
    return default if found is None else float(found)


def reader(world_map: WorldMap, tile_id: str) -> Callable[[str], Any]:
    """A one-argument lookup for one tile, the shape content_rules takes."""
    return lambda name: value(world_map, tile_id, name)
