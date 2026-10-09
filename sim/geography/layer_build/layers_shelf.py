"""Continental shelf area partitioned between tiles: every shelf point belongs to the tile whose land is nearest."""
import shapely

from .layers_vector import _clipped, sea_zones
from .tiles import read_natural_earth

SITE_SIMPLIFY_METRES = 2000.0
SITE_SPACING_METRES = 20000.0
SITE_ROUNDING_METRES = 100.0  # merges coincident sites, which the Voronoi routine cannot take
SHELF_DEPTH_LAYER = "bathymetry_K_200"


def _sites(lands):
    """{(x, y): tile id} of points spaced along every tile's coast; the first tile to claim a point keeps it."""
    sites = {}
    for tile_id, land in sorted(lands.items()):
        outline = shapely.segmentize(land.simplify(SITE_SIMPLIFY_METRES).boundary, SITE_SPACING_METRES)
        for x, y in shapely.get_coordinates(outline):
            key = (round(x / SITE_ROUNDING_METRES) * SITE_ROUNDING_METRES, round(y / SITE_ROUNDING_METRES) * SITE_ROUNDING_METRES)
            sites.setdefault(key, tile_id)
    return sites


def nearest_land_shares(shelf, lands):
    """{tile id: area of the shelf closer to that tile's land than to any other tile's}; shapely shapes in a plane."""
    sites = _sites(lands)
    totals = {tile_id: 0.0 for tile_id in lands}
    if len(sites) < 2:
        for tile_id in totals:
            totals[tile_id] = shelf.area / max(1, len(totals))
        return totals
    owner_of = list(sites.values())
    cells = shapely.get_parts(shapely.voronoi_polygons(shapely.MultiPoint(list(sites)), ordered=True))
    parts = shapely.get_parts(shelf)
    part_index, cell_index = shapely.STRtree(cells).query(parts, predicate="intersects")
    areas = shapely.area(shapely.intersection(parts[part_index], cells[cell_index]))
    for index, area in zip(cell_index, areas):
        totals[owner_of[index]] += area
    return totals


def shelf_area_km2(tiles, side, cache_dir, source):
    deep = read_natural_earth(source, "10m", "physical", SHELF_DEPTH_LAYER, cache_dir)
    result = {tile.tile_id: 0.0 for tile in tiles}
    shelves, lands = [], {}
    for tile, zone, sea in sea_zones(tiles, side, cache_dir, source):
        shelves.append(shapely.make_valid(sea.difference(shapely.union_all(_clipped(deep, zone)))))
        lands[tile.tile_id] = tile.land
    if lands:
        for tile_id, area in nearest_land_shares(shapely.union_all(shelves, grid_size=1.0), lands).items():
            result[tile_id] = area / 1e6
    return result
