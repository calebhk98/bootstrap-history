"""Layer registry: how each layer is computed and how it is described in its file."""
from collections import namedtuple

from . import layers_ocean, layers_raster, layers_vector

Layer = namedtuple("Layer", "compute needs_side unit doc source method conf decimals")

WORLDCLIM = ("WorldClim 2.1 (Fick and Hijmans 2017, Int. J. Climatol. 37:4302), 10 arc-minute, "
             "1970-2000 climatology, https://worldclim.org/data/worldclim21.html")
LAND_SAMPLING = ("Pixel centres falling on the tile's land (cell clipped to Natural Earth 1:50m land), "
                 "weighted by cos(latitude); slivers with no pixel centre widen the land by up to a few pixels.")
NATURAL_EARTH = "Natural Earth 1:10m physical vectors (public domain), https://www.naturalearthdata.com"
SHELF_RULE = ("Zone = the tile's cell plus everything within one cell side (distance in EPSG:6933) of the tile's "
              "land; the ocean part of the zone (Natural Earth bathymetry L_0) minus the part deeper than 200 m "
              "(bathymetry K_200). Tiles whose cell has no sea of their own get 0. Zones of neighbouring tiles "
              "overlap, so values are not additive.")

LAYERS = {
    "mean_temperature_c": Layer(
        layers_raster.mean_temperature_c, False, "degC",
        "Area-mean annual mean air temperature over the tile's land.",
        WORLDCLIM + ", variable bio1", LAND_SAMPLING, "B", 1),
    "annual_precipitation_mm": Layer(
        layers_raster.annual_precipitation_mm, False, "mm/yr",
        "Area-mean annual precipitation over the tile's land.",
        WORLDCLIM + ", variable bio12", LAND_SAMPLING, "B", 0),
    "coldest_month_temperature_c": Layer(
        layers_raster.coldest_month_temperature_c, False, "degC",
        "Area-mean temperature of the coldest month (per pixel) over the tile's land.",
        WORLDCLIM + ", monthly tavg", "Per pixel the minimum of the 12 monthly mean temperatures, then: " + LAND_SAMPLING, "B", 1),
    "warmest_month_temperature_c": Layer(
        layers_raster.warmest_month_temperature_c, False, "degC",
        "Area-mean temperature of the warmest month (per pixel) over the tile's land.",
        WORLDCLIM + ", monthly tavg", "Per pixel the maximum of the 12 monthly mean temperatures, then: " + LAND_SAMPLING, "B", 1),
    "elevation_mean_m": Layer(
        layers_raster.elevation_mean_m, False, "m",
        "Area-mean land elevation above sea level.",
        WORLDCLIM + ", elevation (SRTM-derived)", LAND_SAMPLING, "B", 0),
    "elevation_std_m": Layer(
        layers_raster.elevation_std_m, False, "m",
        "Standard deviation of land elevation within the tile, a ruggedness proxy.",
        WORLDCLIM + ", elevation (SRTM-derived)", "Weighted standard deviation of pixel elevations. " + LAND_SAMPLING, "B", 0),
    "ruggedness_index": Layer(
        layers_raster.ruggedness_index, False, "m",
        "Area-mean of the mean absolute elevation difference between neighbouring raster cells.",
        WORLDCLIM + ", elevation (SRTM-derived)",
        "Per pixel the mean absolute difference to its valid 8 neighbours (a Riley-style index at 10 arc-minute "
        "scale, so coarse), then: " + LAND_SAMPLING, "B", 0),
    "river_km_navigable": Layer(
        layers_vector.river_km_navigable, False, "km",
        "Length of larger rivers inside the tile's cell.",
        NATURAL_EARTH + " (rivers_lake_centerlines)",
        "Features of class River or Canal with scalerank <= %d, clipped to the cell in EPSG:6933, length on the "
        "WGS 84 ellipsoid. Lake centerlines excluded." % layers_vector.NAVIGABLE_MAX_SCALERANK, "C", 0),
    "river_km_all": Layer(
        layers_vector.river_km_all, False, "km",
        "Length of all mapped river centerlines inside the tile's cell.",
        NATURAL_EARTH + " (rivers_lake_centerlines)",
        "All River, intermittent River and Canal features, clipped to the cell, ellipsoidal length. "
        "Lake centerlines excluded.", "C", 0),
    "lake_area_km2": Layer(
        layers_vector.lake_area_km2, False, "km2",
        "Area of lakes inside the tile's cell.",
        NATURAL_EARTH + " (lakes)", "Lake polygons clipped to the cell; planar area in the equal-area plane.", "B", 0),
    "forest_fraction": Layer(
        layers_raster.forest_fraction, False, "fraction",
        "Share of the tile's land under tree cover (present-day land cover, not potential vegetation).",
        "ESA WorldCover 2020 tree-cover fraction at 30 arc-seconds as redistributed by geodata "
        "(https://geodata.ucdavis.edu/geodata/landuse/WorldCover_trees_30s.tif); Zanaga et al. 2021",
        "Raster averaged to about 5 arc-minutes, then: " + LAND_SAMPLING + " Coverage ends at 60S and 84N.", "C", 3),
    "shelf_area_km2": Layer(
        layers_vector.shelf_area_km2, True, "km2",
        "Sea area shallower than 200 m near the tile.",
        NATURAL_EARTH + " (bathymetry_L_0, bathymetry_K_200)", SHELF_RULE, "C", 0),
    "ocean_productivity_gc_m2_yr": Layer(
        layers_ocean.ocean_productivity_gc_m2_yr, True, "gC/m2/yr",
        "Mean ocean net primary productivity of the sea adjacent to the tile.",
        "Oregon State VGPM (Behrenfeld and Falkowski 1997), MODIS r2022 monthly, 2022, "
        "http://sites.science.oregonstate.edu/ocean.productivity",
        "Monthly mg C/m2/day averaged over the 11 months published (April absent upstream), months without "
        "retrieval counted as zero, scaled to a year; then averaged over the sea pixels in the shelf zone "
        "(see shelf_area_km2). Tiles with no sea of their own get 0.", "C", 0),
    "coast_km": Layer(
        layers_vector.coast_km, False, "km",
        "Length of coastline inside the tile's cell.",
        NATURAL_EARTH + " (coastline)", "Coastline clipped to the cell in EPSG:6933, ellipsoidal length; "
        "depends on the 1:10m generalisation.", "C", 0),
}
