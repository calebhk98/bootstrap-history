"""Zonal statistics: sample a lon/lat raster at pixel centres inside a plane geometry."""
import math

import numpy
import rasterio
import shapely
from rasterio.enums import Resampling

from .tiles import plane_x, plane_y


class Grid:
    """A north-up lon/lat raster whose pixel centres are mapped into the plane."""

    def __init__(self, array, transform):
        self.array = numpy.asarray(array, dtype=numpy.float64)
        rows, columns = self.array.shape
        longitudes = transform.c + (numpy.arange(columns) + 0.5) * transform.a
        latitudes = transform.f + (numpy.arange(rows) + 0.5) * transform.e
        self.x = numpy.asarray(plane_x(longitudes))
        self.y = numpy.asarray(plane_y(latitudes))
        self.row_weight = numpy.cos(numpy.radians(latitudes))
        self.pixel_metres = abs(self.x[1] - self.x[0])

    def sample(self, geometry, widen=True):
        """(values, weights) of valid pixels inside geometry; `widen` retries a sliver with a buffer."""
        if geometry.is_empty:
            return numpy.array([]), numpy.array([])
        for buffer_pixels in ((0.0, 1.5, 4.0) if widen else (0.0,)):
            shape = geometry.buffer(buffer_pixels * self.pixel_metres) if buffer_pixels else geometry
            values, weights = self._inside(shape)
            if len(values):
                return values, weights
        return numpy.array([]), numpy.array([])

    def _inside(self, geometry):
        min_x, min_y, max_x, max_y = geometry.bounds
        first_column = numpy.searchsorted(self.x, min_x)
        last_column = numpy.searchsorted(self.x, max_x, side="right")
        first_row = numpy.searchsorted(-self.y, -max_y)
        last_row = numpy.searchsorted(-self.y, -min_y, side="right")
        if first_column >= last_column or first_row >= last_row:
            return numpy.array([]), numpy.array([])
        grid_x, grid_y = numpy.meshgrid(self.x[first_column:last_column], self.y[first_row:last_row])
        inside = shapely.contains_xy(geometry, grid_x, grid_y)
        block = self.array[first_row:last_row, first_column:last_column]
        weight = numpy.broadcast_to(self.row_weight[first_row:last_row, None], block.shape)
        keep = inside & numpy.isfinite(block)
        return block[keep], weight[keep]


def weighted_mean(values, weights, empty=0.0):
    """Weighted mean, or `empty` with no samples."""
    return float(numpy.average(values, weights=weights)) if len(values) else empty


def weighted_std(values, weights, empty=0.0):
    """Weighted standard deviation, or `empty` with no samples."""
    if not len(values):
        return empty
    mean = numpy.average(values, weights=weights)
    return float(math.sqrt(numpy.average((values - mean) ** 2, weights=weights)))


def read_band(path, band=1, width=None):
    """(array with NaN for nodata, transform), optionally averaged down to `width` columns."""
    with rasterio.open(path) as source:
        shape = None
        if width and source.width > width:
            shape = (max(1, round(source.height * width / source.width)), width)
        data = source.read(band, out_shape=shape, resampling=Resampling.average).astype(numpy.float64)
        transform = source.transform if shape is None else source.transform * source.transform.scale(
            source.width / shape[1], source.height / shape[0])
        if source.nodata is not None and not math.isnan(source.nodata):
            data[data == source.nodata] = numpy.nan
    data[data < -1e30] = numpy.nan
    return data, transform
