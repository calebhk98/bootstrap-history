"""Ocean productivity layer from the Oregon State VGPM monthly climatology."""
import gzip
import os
import shutil

import numpy
from rasterio.transform import from_origin

from sim.unit_conversions import CIVIL_DAYS_PER_YEAR

from .cache import fetch
from .layers_vector import sea_zones
from .zonal import Grid, weighted_mean

VGPM_YEAR = 2022
# Start day of each month the archive holds (the April file is absent upstream).
VGPM_DAYS = (1, 32, 60, 121, 152, 182, 213, 244, 274, 305, 335)
MILLIGRAMS_PER_GRAM = 1000.0


def _monthly_array(cache_dir, source, day):
    from pyhdf.SD import SD  # build-only dependency
    name = "vgpm.%d%03d.hdf" % (VGPM_YEAR, day)
    path = os.path.join(cache_dir, name)
    if not os.path.exists(path):
        archive = fetch("%s/%s.gz" % (source.files["monthly_archive"], name), cache_dir)
        with gzip.open(archive, "rb") as source, open(path, "wb") as target:
            shutil.copyfileobj(source, target)
    array = SD(path).select("npp")[:].astype(numpy.float64)
    array[array < 0] = numpy.nan
    return array


def annual_npp_grid(cache_dir, source):
    """Annual NPP in g C per m2 per year; sea pixels with no retrieval in a month count as zero."""
    stack = numpy.stack([_monthly_array(cache_dir, source, day) for day in VGPM_DAYS])
    sea = numpy.isfinite(stack).any(axis=0)
    mean_rate = numpy.nan_to_num(stack).mean(axis=0)  # mg C per m2 per day
    annual = mean_rate * CIVIL_DAYS_PER_YEAR / MILLIGRAMS_PER_GRAM
    annual[~sea] = numpy.nan
    rows, columns = annual.shape
    return Grid(annual, from_origin(-180.0, 90.0, 360.0 / columns, 180.0 / rows))


def ocean_productivity_gc_m2_yr(tiles, side, cache_dir, source):
    grid = annual_npp_grid(cache_dir, source)
    result = {tile.tile_id: 0.0 for tile in tiles}
    for tile, zone, _sea in sea_zones(tiles, side, cache_dir, source):
        values, weights = grid.sample(zone, widen=False)
        result[tile.tile_id] = weighted_mean(values, weights)
    return result
