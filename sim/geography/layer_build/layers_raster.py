"""Layers sampled from rasters over each tile's land: climate, relief, tree cover."""
import numpy

from .cache import fetch, fetch_unzipped
from .zonal import Grid, read_band, weighted_mean, weighted_std

TREE_COVER_WIDTH = 4320  # averaged down from the native 30 arc-second grid


def _worldclim_grid(cache_dir, source, archive, member):
    directory = fetch_unzipped("%s/%s.zip" % (source.files["base"], archive), cache_dir)
    array, transform = read_band("%s/%s.tif" % (directory, member))
    return Grid(array, transform)


def _land_means(tiles, grid, scale=1.0):
    return {tile.tile_id: weighted_mean(*grid.sample(tile.land)) * scale for tile in tiles}


def _monthly_extreme(cache_dir, source, pick):
    stack = []
    transform = None
    for month in range(1, 13):
        array, transform = read_band("%s/wc2.1_10m_tavg_%02d.tif" % (
            fetch_unzipped("%s/wc2.1_10m_tavg.zip" % source.files["base"], cache_dir), month))
        stack.append(array)
    return Grid(pick(numpy.stack(stack), axis=0), transform)


def mean_temperature_c(tiles, cache_dir, source):
    return _land_means(tiles, _worldclim_grid(cache_dir, source, "wc2.1_10m_bio", "wc2.1_10m_bio_1"))


def annual_precipitation_mm(tiles, cache_dir, source):
    return _land_means(tiles, _worldclim_grid(cache_dir, source, "wc2.1_10m_bio", "wc2.1_10m_bio_12"))


def coldest_month_temperature_c(tiles, cache_dir, source):
    return _land_means(tiles, _monthly_extreme(cache_dir, source, numpy.min))


def warmest_month_temperature_c(tiles, cache_dir, source):
    return _land_means(tiles, _monthly_extreme(cache_dir, source, numpy.max))


def _elevation_grid(cache_dir, source):
    return _worldclim_grid(cache_dir, source, "wc2.1_10m_elev", "wc2.1_10m_elev")


def elevation_mean_m(tiles, cache_dir, source):
    return _land_means(tiles, _elevation_grid(cache_dir, source))


def elevation_std_m(tiles, cache_dir, source):
    grid = _elevation_grid(cache_dir, source)
    return {tile.tile_id: weighted_std(*grid.sample(tile.land)) for tile in tiles}


def roughness_grid(grid):
    """Per-pixel mean absolute elevation difference to the valid 8 neighbours."""
    padded = numpy.pad(grid.array, 1, mode="constant", constant_values=numpy.nan)
    rows, columns = grid.array.shape
    total = numpy.zeros((rows, columns))
    count = numpy.zeros((rows, columns))
    for row_shift in (-1, 0, 1):
        for column_shift in (-1, 0, 1):
            if row_shift == 0 and column_shift == 0:
                continue
            neighbour = padded[1 + row_shift:1 + row_shift + rows, 1 + column_shift:1 + column_shift + columns]
            difference = numpy.abs(neighbour - grid.array)
            valid = numpy.isfinite(difference)
            total[valid] += difference[valid]
            count[valid] += 1
    result = numpy.full((rows, columns), numpy.nan)
    numpy.divide(total, count, out=result, where=count > 0)
    result[~numpy.isfinite(grid.array)] = numpy.nan
    return result


def ruggedness_index(tiles, cache_dir, source):
    grid = _elevation_grid(cache_dir, source)
    grid.array = roughness_grid(grid)
    return _land_means(tiles, grid)


def forest_fraction(tiles, cache_dir, source):
    array, transform = read_band(fetch(source.files["tree_cover"], cache_dir), width=TREE_COVER_WIDTH)
    if numpy.nanmax(array) > 1.5:
        array = array / 100.0
    grid = Grid(numpy.clip(array, 0.0, 1.0), transform)
    return _land_means(tiles, grid)
