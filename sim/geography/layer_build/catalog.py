"""Layer catalogue: how each layer is described in its file. Datasets and loaders are in sim/geography/map_data_sources.py."""
from collections import namedtuple

NAVIGABLE_MAX_SCALERANK = 6  # Natural Earth rank: lower is a larger river
CELL_DEGREES = 0.1  # ocean raster cell of the port and sea link build

Layer = namedtuple("Layer", "needs_side unit doc method conf decimals")

LAND_SAMPLING = ("Pixel centres falling on the tile's land (cell clipped to Natural Earth 1:50m land), "
                 "weighted by cos(latitude); slivers with no pixel centre widen the land by up to a few pixels.")
SHELF_RULE = ("Zone = the tile's cell plus everything within one cell side (distance in EPSG:6933) of the tile's "
              "land; the ocean part of the zone (Natural Earth bathymetry L_0) minus the part deeper than 200 m "
              "(bathymetry K_200). Tiles whose cell has no sea of their own get 0. Zones of neighbouring tiles "
              "overlap, so values are not additive.")

LAYERS = {
    "mean_temperature_c": Layer(
        False, "degC",
        "Area-mean annual mean air temperature over the tile's land.",
        LAND_SAMPLING, "B", 1),
    "annual_precipitation_mm": Layer(
        False, "mm/yr",
        "Area-mean annual precipitation over the tile's land.",
        LAND_SAMPLING, "B", 0),
    "coldest_month_temperature_c": Layer(
        False, "degC",
        "Area-mean temperature of the coldest month (per pixel) over the tile's land.",
        "Per pixel the minimum of the 12 monthly mean temperatures, then: " + LAND_SAMPLING, "B", 1),
    "warmest_month_temperature_c": Layer(
        False, "degC",
        "Area-mean temperature of the warmest month (per pixel) over the tile's land.",
        "Per pixel the maximum of the 12 monthly mean temperatures, then: " + LAND_SAMPLING, "B", 1),
    "elevation_mean_m": Layer(
        False, "m",
        "Area-mean land elevation above sea level.",
        LAND_SAMPLING, "B", 0),
    "elevation_std_m": Layer(
        False, "m",
        "Standard deviation of land elevation within the tile, a ruggedness proxy.",
        "Weighted standard deviation of pixel elevations. " + LAND_SAMPLING, "B", 0),
    "ruggedness_index": Layer(
        False, "m",
        "Area-mean of the mean absolute elevation difference between neighbouring raster cells.",
        "Per pixel the mean absolute difference to its valid 8 neighbours (a Riley-style index at 10 arc-minute "
        "scale, so coarse), then: " + LAND_SAMPLING, "B", 0),
    "river_km_navigable": Layer(
        False, "km",
        "Length of larger rivers inside the tile's cell.",
        "Features of class River or Canal with scalerank <= %d, clipped to the cell in EPSG:6933, length on the "
        "WGS 84 ellipsoid. Lake centerlines excluded." % NAVIGABLE_MAX_SCALERANK, "C", 0),
    "river_km_all": Layer(
        False, "km",
        "Length of all mapped river centerlines inside the tile's cell.",
        "All River, intermittent River and Canal features, clipped to the cell, ellipsoidal length. "
        "Lake centerlines excluded.", "C", 0),
    "lake_area_km2": Layer(
        False, "km2",
        "Area of lakes inside the tile's cell.",
        "Lake polygons clipped to the cell; planar area in the equal-area plane.", "B", 0),
    "forest_fraction": Layer(
        False, "fraction",
        "Share of the tile's land under tree cover (present-day land cover, not potential vegetation).",
        "Raster averaged to about 5 arc-minutes, then: " + LAND_SAMPLING + " Coverage ends at 60S and 84N.", "C", 3),
    "shelf_area_km2": Layer(
        True, "km2",
        "Sea area shallower than 200 m near the tile.",
        SHELF_RULE, "C", 0),
    "ocean_productivity_gc_m2_yr": Layer(
        True, "gC/m2/yr",
        "Mean ocean net primary productivity of the sea adjacent to the tile.",
        "Monthly mg C/m2/day averaged over the 11 months published (April absent upstream), months without "
        "retrieval counted as zero, scaled to a year; then averaged over the sea pixels in the shelf zone "
        "(see shelf_area_km2). Tiles with no sea of their own get 0.", "C", 0),
    "coast_km": Layer(
        False, "km",
        "Length of coastline inside the tile's cell.",
        "Coastline clipped to the cell in EPSG:6933, ellipsoidal length; "
        "depends on the 1:10m generalisation.", "C", 0),
    "is_port": Layer(
        False, "flag",
        "1 when the tile's own land touches the ocean (so ships can put in), else 0.",
        "Ocean polygon rasterised on a %.1f degree grid, any touched cell counted as water, "
        "only the largest connected body kept (lakes and the Caspian drop out); the tile is a port when a water "
        "cell within one cell of its land is left after tiles claim cells (see sea_links)." % CELL_DEGREES, "C", 0),
}
