"""Which tiles a holding resolves to, and each tile's land figures, read from the map.

A civilisation holds the tiles it lists (`home_tiles`), or those its region labels name; a region is the
per-tile `region` value, so the set of tiles is whatever the map says carries that label.
"""
import functools
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from sim.geography import map_source, tile_layers

HECTARES_PER_KM2 = 100.0


def _map(world_map: Optional[map_source.WorldMap]) -> map_source.WorldMap:
    return world_map if world_map is not None else map_source.load_map()


@functools.lru_cache(maxsize=8)
def _tiles_by_region(world_map: map_source.WorldMap) -> Dict[str, Tuple[str, ...]]:
    grouped: Dict[str, List[str]] = {}
    for tile_id in world_map.tiles:
        region = tile_layers.value(world_map, tile_id, "region")
        if region:
            grouped.setdefault(region, []).append(tile_id)
    return {region: tuple(sorted(tile_ids)) for region, tile_ids in grouped.items()}


def tiles_of_regions(regions: Iterable[str], world_map: Optional[map_source.WorldMap] = None) -> List[str]:
    """Sorted, deduplicated tiles carrying any of these region labels (unknown labels add none)."""
    grouped = _tiles_by_region(_map(world_map))
    return sorted({tile_id for region in regions for tile_id in grouped.get(region, ())})


def tiles_held(civilisation: Mapping[str, Any], world_map: Optional[map_source.WorldMap] = None) -> List[str]:
    """The tiles a civilisation holds: those it lists as `home_tiles`, else the tiles its `home_regions`
    labels name (a region is only a label over tiles). Sorted; tiles the map lacks are not held."""
    world_map = _map(world_map)
    listed = civilisation.get("home_tiles")
    if listed is None:
        return tiles_of_regions(civilisation.get("home_regions") or [], world_map)
    return sorted({tile_id for tile_id in listed if tile_id in world_map.tiles})


def regions_of_tiles(tile_ids: Iterable[str], world_map: Optional[map_source.WorldMap] = None) -> List[str]:
    """Sorted region labels carried by these tiles (a tile with no label adds none)."""
    world_map = _map(world_map)
    labels = {tile_layers.value(world_map, tile_id, "region") for tile_id in tile_ids if tile_id in world_map.tiles}
    return sorted(label for label in labels if label)


def region_ids(world_map: Optional[map_source.WorldMap] = None) -> List[str]:
    """Every region label some tile of the map carries, sorted."""
    return sorted(_tiles_by_region(_map(world_map)))


def region_has_tiles(region: str, world_map: Optional[map_source.WorldMap] = None) -> bool:
    return bool(_tiles_by_region(_map(world_map)).get(region))


def tile_land(tile_id: str, world_map: Optional[map_source.WorldMap] = None) -> Dict[str, float]:
    """{land_area_km2, arable_fraction, fertility_quality_multiplier, arable_hectares} of a tile."""
    world_map = _map(world_map)
    area = tile_layers.number(world_map, tile_id, "land_area_km2", 0.0)
    arable_fraction = tile_layers.number(world_map, tile_id, "arable_fraction", 0.0)
    return {"land_area_km2": area, "arable_fraction": arable_fraction,
            "fertility_quality_multiplier": tile_layers.number(
                world_map, tile_id, "fertility_quality_multiplier", 0.0),
            "arable_hectares": area * arable_fraction * HECTARES_PER_KM2}


def tile_centre(tile_id: str, world_map: Optional[map_source.WorldMap] = None) -> Tuple[float, float]:
    tile = _map(world_map).tiles[tile_id]
    return float(tile["lat"]), float(tile["lon"])


def neighbours(tile_id: str, world_map: Optional[map_source.WorldMap] = None) -> List[str]:
    return list(_map(world_map).tiles.get(tile_id, {}).get("borders", []))


def edge_km(world_map: Optional[map_source.WorldMap] = None) -> float:
    """Width of a nominal tile: the side of a square of the map's nominal tile area."""
    return math.sqrt(float(_map(world_map).properties.get("target_tile_area_km2", 0.0)))
