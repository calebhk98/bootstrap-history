"""Layers measured from Natural Earth vectors: rivers, lakes, coastline, continental shelf."""
import pyproj
import shapely
from shapely.ops import transform as transform_geometry

from .catalog import NAVIGABLE_MAX_SCALERANK
from .tiles import PLANE_CRS, read_natural_earth

NAVIGABLE_CLASSES = ("River", "Canal")
SEA_IN_CELL_MIN_FRACTION = 0.005  # below this share of the cell a tile has no sea of its own
ZONE_SIMPLIFY_METRES = 2000.0

_GEOD = pyproj.Geod(ellps="WGS84")
_INVERSE = pyproj.Transformer.from_crs(PLANE_CRS, 4326, always_xy=True)


def geodesic_km(geometry):
    """Ellipsoidal length in km of a line geometry given in the plane."""
    if geometry.is_empty:
        return 0.0
    return _GEOD.geometry_length(transform_geometry(_INVERSE.transform, geometry)) / 1000.0


def _clipped(frame, region):
    """Parts of the frame's geometries inside region."""
    shapes = frame.geometry.values
    return [shapely.intersection(shapes[index], region)
            for index in frame.sindex.query(region, predicate="intersects")]


def _line_km(tiles, frame):
    return {tile.tile_id: geodesic_km(shapely.union_all(_clipped(frame, tile.cell))) for tile in tiles}


def _rivers(cache_dir, source):
    frame = read_natural_earth(source, "10m", "physical", "rivers_lake_centerlines", cache_dir)
    return frame[frame["featurecla"] != "Lake Centerline"]


def river_km_all(tiles, cache_dir, source):
    return _line_km(tiles, _rivers(cache_dir, source))


def river_km_navigable(tiles, cache_dir, source):
    frame = _rivers(cache_dir, source)
    keep = frame["featurecla"].isin(NAVIGABLE_CLASSES) & (frame["scalerank"] <= NAVIGABLE_MAX_SCALERANK)
    return _line_km(tiles, frame[keep])


def coast_km(tiles, cache_dir, source):
    return _line_km(tiles, read_natural_earth(source, "10m", "physical", "coastline", cache_dir))


def lake_area_km2(tiles, cache_dir, source):
    frame = read_natural_earth(source, "10m", "physical", "lakes", cache_dir)
    return {tile.tile_id: sum(piece.area for piece in _clipped(frame, tile.cell)) / 1e6 for tile in tiles}


def sea_zones(tiles, side, cache_dir, source):
    """Yield (tile, zone, ocean clipped to zone) for tiles with sea in their own cell.

    The zone is the tile's cell plus everything within one cell side of its land.
    """
    ocean = read_natural_earth(source, "10m", "physical", "bathymetry_L_0", cache_dir)
    for tile in tiles:
        sea_area = sum(piece.area for piece in _clipped(ocean, tile.cell))
        if sea_area < SEA_IN_CELL_MIN_FRACTION * tile.cell.area:
            continue
        reach = tile.land.simplify(ZONE_SIMPLIFY_METRES).buffer(side)
        zone = shapely.union(tile.cell, reach)
        yield tile, zone, shapely.union_all(_clipped(ocean, zone))


def shelf_area_km2(tiles, side, cache_dir, source):
    deep = read_natural_earth(source, "10m", "physical", "bathymetry_K_200", cache_dir)
    result = {tile.tile_id: 0.0 for tile in tiles}
    for tile, zone, sea in sea_zones(tiles, side, cache_dir, source):
        deep_area = sum(piece.area for piece in _clipped(deep, zone))
        result[tile.tile_id] = max(0.0, sea.area - deep_area) / 1e6
    return result
