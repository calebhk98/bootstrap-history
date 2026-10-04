"""Ports and sea links: which tiles reach which by water, from a coarse ocean raster.

Ocean (Natural Earth 1:10m land and coastline) is rasterised on a lon/lat grid; a cell the coastline
crosses counts as water, so narrow straits stay open while isthmuses wider than a cell stay closed. A tile's port cells are water cells next to its own land (inside its majority country,
since a square cell can hold a neighbour's coast). One
multi-source shortest-path pass over the 8-neighbour water grid labels each water cell with its
nearest port tile; two tiles are linked where their labelled regions touch, with the water distance
through the touching pair of cells.
"""
import math

import geopandas
import numpy
import rasterio.features
import scipy.ndimage
import scipy.sparse
import scipy.sparse.csgraph
from rasterio.transform import from_origin

from sim.geography.distance import haversine_km

from .cache import fetch_unzipped
from .tiles import NATURAL_EARTH, PLANE_CRS, read_natural_earth

CELL_DEGREES = 0.1
BRIDGED_GAP_CELLS = 2  # port cells this close (in cells) belong to one coast
LINK_RANGE_KM = 2000.0  # longest water path a link may have
KM_PER_DEGREE = 6371.0 * math.pi / 180.0
NEIGHBOUR_OFFSETS = ((0, 1), (1, 0), (1, 1), (1, -1))  # half of the 8 neighbours; edges are undirected
ALL_NEIGHBOURS = numpy.ones((3, 3), dtype=bool)

_cache = {}


def _ocean_water(cache_dir):
    """Boolean grid (rows north to south) of water cells: centre not on land, or a coastline passes through
    (so a strait narrower than a cell stays open); only the largest connected body is kept, which drops lakes."""
    shape = (round(180 / CELL_DEGREES), round(360 / CELL_DEGREES))
    transform = from_origin(-180.0, 90.0, CELL_DEGREES, CELL_DEGREES)
    land = geopandas.read_file(fetch_unzipped("%s/50m/physical/ne_50m_land.zip" % NATURAL_EARTH, cache_dir) + "/ne_50m_land.shp")
    coast = geopandas.read_file(fetch_unzipped("%s/50m/physical/ne_50m_coastline.zip" % NATURAL_EARTH, cache_dir) + "/ne_50m_coastline.shp")
    on_land = rasterio.features.rasterize(land.geometry.values, out_shape=shape, transform=transform, dtype="uint8").astype(bool)
    on_coast = rasterio.features.rasterize(coast.geometry.values, out_shape=shape, transform=transform,
                                           all_touched=True, dtype="uint8").astype(bool)
    water = ~on_land | on_coast
    labels, count = scipy.ndimage.label(water, structure=ALL_NEIGHBOURS)
    return labels == 1 + int(numpy.argmax(numpy.bincount(labels.ravel())[1:])) if count else water


def _own_land(tile, countries):
    """The tile's land inside its majority country (all its land when the country is unknown)."""
    shape = countries.get(tile.country)
    own = tile.land.intersection(shape) if shape is not None else tile.land
    return own if not own.is_empty else tile.land


def _countries(cache_dir):
    """{Natural Earth country name: shape in the plane}."""
    frame = read_natural_earth("50m", "cultural", "admin_0_countries", cache_dir)
    return dict(zip(frame["NAME"], frame.geometry.values))


def _port_cells(tiles, water, countries):
    """{tile_id: [flat cell index]}: water cells within one cell of the tile's land that no nearer tile centre claims."""
    rows, columns = water.shape
    lands = geopandas.GeoSeries([_own_land(tile, countries) for tile in tiles], crs=PLANE_CRS).to_crs(4326)
    wanted = {}
    for tile, land in zip(tiles, lands):
        if land.is_empty:
            continue
        west, south, east, north = land.bounds
        column0 = max(0, int((west + 180) / CELL_DEGREES) - 2)
        column1 = min(columns, int((east + 180) / CELL_DEGREES) + 3)
        row0 = max(0, int((90 - north) / CELL_DEGREES) - 2)
        row1 = min(rows, int((90 - south) / CELL_DEGREES) + 3)
        window = from_origin(-180.0 + column0 * CELL_DEGREES, 90.0 - row0 * CELL_DEGREES, CELL_DEGREES, CELL_DEGREES)
        owned = rasterio.features.rasterize([land], out_shape=(row1 - row0, column1 - column0),
                                            transform=window, dtype="uint8").astype(bool)
        if not owned.any():  # land smaller than a cell: every cell it touches counts
            owned = rasterio.features.rasterize([land], out_shape=(row1 - row0, column1 - column0),
                                                transform=window, all_touched=True, dtype="uint8").astype(bool)
        near = scipy.ndimage.binary_dilation(owned, structure=ALL_NEIGHBOURS) & water[row0:row1, column0:column1]
        local_rows, local_columns = numpy.nonzero(near)
        if len(local_rows):
            wanted[tile.tile_id] = [(row0 + r) * columns + column0 + c for r, c in zip(local_rows, local_columns)]
    best, ports = {}, {}  # a cell goes to the candidate tile whose centre is nearest, so a tile's cell does not serve a neighbour's coast
    for tile in tiles:
        for cell in wanted.get(tile.tile_id, ()):
            latitude, longitude = 90.0 - (cell // columns + 0.5) * CELL_DEGREES, -180.0 + (cell % columns + 0.5) * CELL_DEGREES
            offset = math.hypot(latitude - tile.latitude, (longitude - tile.longitude) * math.cos(math.radians(latitude)))
            if cell not in best or offset < best[cell][0]:
                best[cell] = (offset, tile.tile_id)
    for cell, (_offset, tile_id) in best.items():
        ports.setdefault(tile_id, []).append(cell)
    return {tile_id: _main_coast(cells, columns) for tile_id, cells in ports.items()}


def _main_coast(cells, columns):
    """The tile's largest stretch of port cells (gaps up to a few cells bridged). A tile is one graph node, so a
    second coast on another sea (Sinai, Panama) would let ships cut across the tile; only the main coast is kept."""
    rows_of, columns_of = numpy.divmod(numpy.array(cells), columns)
    grid = numpy.zeros((rows_of.max() - rows_of.min() + 1, columns_of.max() - columns_of.min() + 1), dtype=bool)
    grid[rows_of - rows_of.min(), columns_of - columns_of.min()] = True
    labels, _count = scipy.ndimage.label(scipy.ndimage.binary_dilation(grid, structure=numpy.ones((3, 3), dtype=bool), iterations=BRIDGED_GAP_CELLS))
    label_of_cell = labels[rows_of - rows_of.min(), columns_of - columns_of.min()]
    main = numpy.argmax(numpy.bincount(label_of_cell))
    return [cell for cell, label in zip(cells, label_of_cell) if label == main]


def _water_graph(water):
    """(graph of step km over water nodes, flat cell of each node, node of each flat cell, edge arrays)."""
    rows, columns = water.shape
    cells = numpy.flatnonzero(water.ravel())
    node_of = numpy.full(rows * columns, -1, dtype=numpy.int64)
    node_of[cells] = numpy.arange(len(cells))
    row, column = numpy.divmod(cells, columns)
    latitude = numpy.radians(90.0 - (row + 0.5) * CELL_DEGREES)
    starts, ends, lengths = [], [], []
    for row_step, column_step in NEIGHBOUR_OFFSETS:
        other_row, other_column = row + row_step, column + column_step
        inside = (other_row < rows) & (other_column >= 0) & (other_column < columns)
        other = numpy.full(len(cells), -1, dtype=numpy.int64)
        other[inside] = node_of[other_row[inside] * columns + other_column[inside]]
        keep = other >= 0
        north_south = row_step * CELL_DEGREES * KM_PER_DEGREE
        east_west = column_step * CELL_DEGREES * KM_PER_DEGREE * numpy.cos(latitude[keep] - row_step * math.radians(CELL_DEGREES) / 2)
        starts.append(numpy.flatnonzero(keep))
        ends.append(other[keep])
        lengths.append(numpy.hypot(north_south, east_west))
    starts, ends, lengths = (numpy.concatenate(part) for part in (starts, ends, lengths))
    graph = scipy.sparse.csr_matrix((lengths, (starts, ends)), shape=(len(cells), len(cells)))
    return graph, cells, node_of, (starts, ends, lengths)


def _trace(node, predecessors):
    path = [node]
    while predecessors[path[-1]] >= 0:
        path.append(predecessors[path[-1]])
    return path


def _position(cell, columns):
    return 90.0 - (cell // columns + 0.5) * CELL_DEGREES, -180.0 + (cell % columns + 0.5) * CELL_DEGREES


def _anchor(cells, columns):
    """The port cell nearest the mean of the tile's port cells: where goods of the tile reach the water."""
    positions = numpy.array([_position(cell, columns) for cell in cells])
    return _position(cells[int(numpy.argmin(((positions - positions.mean(axis=0)) ** 2).sum(axis=1)))], columns)


def _entry(pair, total, path, along, shore_km, cells, columns, anchors):
    """A link; its km adds the straight run from each tile's anchor to the port cell the water path leaves from."""
    middle = cells[path[min(int(numpy.searchsorted(along, total / 2)), len(path) - 1)]]
    access = sum(haversine_km(*anchors[tile_id], *_position(cells[end], columns)) for tile_id, end in zip(pair, (path[0], path[-1])))
    return {"id": "%s|%s" % pair, "tile_a": pair[0], "tile_b": pair[1], "water_km": round(float(total + access)),
            "midpoint_lat": round(90.0 - (middle // columns + 0.5) * CELL_DEGREES, 2),
            "midpoint_lon": round(-180.0 + (middle % columns + 0.5) * CELL_DEGREES, 2),
            "max_offshore_km": round(float(shore_km[path].max()))}


def network(tiles, cache_dir):
    """(set of port tile ids, sorted list of link entries), computed once per build."""
    if cache_dir in _cache:
        return _cache[cache_dir]
    water = _ocean_water(cache_dir)
    columns = water.shape[1]
    ports = _port_cells(tiles, water, _countries(cache_dir))
    graph, cells, node_of, (edge_from, edge_to, edge_km) = _water_graph(water)
    coast = numpy.flatnonzero((scipy.ndimage.binary_dilation(~water, structure=ALL_NEIGHBOURS) & water).ravel())
    shore_km = scipy.sparse.csgraph.dijkstra(graph, directed=False, indices=node_of[coast], min_only=True)
    tile_ids = sorted(ports)
    source_nodes = [node_of[cell] for tile_id in tile_ids for cell in ports[tile_id]]
    tile_of_node = numpy.full(len(cells), -1, dtype=numpy.int64)
    tile_of_node[source_nodes] = [index for index, tile_id in enumerate(tile_ids) for _cell in ports[tile_id]]
    distance, predecessors, origin = scipy.sparse.csgraph.dijkstra(
        graph, directed=False, indices=source_nodes, min_only=True, return_predecessors=True, limit=LINK_RANGE_KM / 2)
    owner = numpy.where(origin >= 0, tile_of_node[numpy.maximum(origin, 0)], -1)
    crossing = (owner[edge_from] >= 0) & (owner[edge_to] >= 0) & (owner[edge_from] != owner[edge_to])
    start, end = edge_from[crossing], edge_to[crossing]
    total = distance[start] + edge_km[crossing] + distance[end]
    low, high = numpy.minimum(owner[start], owner[end]), numpy.maximum(owner[start], owner[end])
    order = numpy.lexsort((total, high, low))
    first = numpy.ones(len(order), dtype=bool)
    first[1:] = (low[order][1:] != low[order][:-1]) | (high[order][1:] != high[order][:-1])
    anchors = {tile_id: _anchor(ports[tile_id], columns) for tile_id in tile_ids}
    entries = []
    for index in order[first]:
        if total[index] > LINK_RANGE_KM:
            continue
        near_low, near_high = (start[index], end[index]) if owner[start[index]] == low[index] else (end[index], start[index])
        side_low, side_high = _trace(near_low, predecessors), _trace(near_high, predecessors)
        path = numpy.array(side_low[::-1] + side_high)
        along = numpy.concatenate((distance[side_low[::-1]], total[index] - distance[side_high]))
        entries.append(_entry((tile_ids[low[index]], tile_ids[high[index]]), total[index], path, along, shore_km, cells, columns, anchors))
    entries.sort(key=lambda entry: entry["id"])
    _cache[cache_dir] = (set(tile_ids), entries)
    return _cache[cache_dir]


def is_port(tiles, cache_dir):
    ports = network(tiles, cache_dir)[0]
    return {tile.tile_id: 1 if tile.tile_id in ports else 0 for tile in tiles}
