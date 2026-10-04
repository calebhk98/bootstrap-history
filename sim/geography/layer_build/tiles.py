"""Tile cells in the equal-area plane, clipped to land (same rule as the tile generator)."""
import json
import math
import os

import geopandas
import pyproj
import shapely
from shapely.geometry import Point, box

from .cache import fetch_unzipped

PLANE_CRS = 6933  # WGS 84 / NSIDC EASE-Grid 2.0 Global (cylindrical equal area)
NATURAL_EARTH = "https://naciscdn.org/naturalearth"
GEOGRAPHY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "world", "geography.json")

_FORWARD = pyproj.Transformer.from_crs(4326, PLANE_CRS, always_xy=True)


def plane_x(longitudes):
    """Plane x for longitudes (the projection is separable in x and y)."""
    return _FORWARD.transform(longitudes, [0.0] * len(longitudes))[0]


def plane_y(latitudes):
    """Plane y for latitudes."""
    return _FORWARD.transform([0.0] * len(latitudes), latitudes)[1]


def read_natural_earth(scale, theme, name, cache_dir):
    """A Natural Earth layer as a GeoDataFrame in the plane CRS."""
    stem = "ne_%s_%s" % (scale, name)
    directory = fetch_unzipped("%s/%s/%s/%s.zip" % (NATURAL_EARTH, scale, theme, stem), cache_dir)
    return geopandas.read_file(os.path.join(directory, stem + ".shp")).to_crs(PLANE_CRS)


class Tile:
    """One grid cell: its cell box and its land (cell clipped to land)."""

    def __init__(self, tile_id, record, cell, land):
        self.tile_id = tile_id
        self.latitude = record["lat"]
        self.longitude = record["lon"]
        self.cell = cell
        self.land = land


def load_tiles(cache_dir, geography_path=GEOGRAPHY_PATH):
    """Tiles of geography.json's land_tiles, with cell and land geometry."""
    with open(geography_path, encoding="utf-8") as handle:
        section = json.load(handle)["land_tiles"]
    side = math.sqrt(section["target_tile_area_km2"]) * 1000.0
    land_frame = read_natural_earth("50m", "physical", "land", cache_dir)
    land_index = land_frame.sindex
    land_shapes = land_frame.geometry.values
    tiles = []
    for tile_id in sorted(section["tiles"]):
        record = section["tiles"][tile_id]
        point = geopandas.GeoSeries([Point(record["lon"], record["lat"])], crs=4326).to_crs(PLANE_CRS).iloc[0]
        column = math.floor(point.x / side)
        row = math.floor(point.y / side)
        cell = box(column * side, row * side, (column + 1) * side, (row + 1) * side)
        pieces = [shapely.intersection(land_shapes[index], cell)
                  for index in land_index.query(cell, predicate="intersects")]
        land = shapely.union_all(pieces) if pieces else shapely.Polygon()
        tiles.append(Tile(tile_id, record, cell, land))
    return tiles, side
