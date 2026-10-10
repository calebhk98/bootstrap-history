"""Registry of the dataset behind each generated map layer.

One entry per layer, one option per dataset that can fill it; the first option of a layer is its default,
the dataset the committed files were built from. An option names the loader that computes the layer
(`module:function`, imported on use so this module needs no build dependency), the files or URLs the
loader reads (`files`), and the text written into the layer file's `source` field. Swapping a layer's
dataset means adding an option here, with its loader and files, and choosing it with
`--source layer=option` on the tile generator or the layer build.

A loader is called as `loader(tiles, cache_dir, source)`, or `loader(tiles, side, cache_dir, source)` for
layers whose catalogue entry sets `needs_side` (sim/geography/layer_build/catalog.py). The tile-grid
layers are not computed by loaders of that shape: their loader builds the helper the tile generator uses
(tools/generate_geography_tiles.py).
"""
import importlib
from collections import namedtuple

Source = namedtuple("Source", "dataset provider citation url terms loader source_text files")

NATURAL_EARTH_BASE = "https://naciscdn.org/naturalearth"
NATURAL_EARTH_TERMS = "public domain"
NATURAL_EARTH_TEXT = "Natural Earth 1:10m physical vectors (public domain), https://www.naturalearthdata.com"
WORLDCLIM_BASE = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base"
WORLDCLIM_TEXT = ("WorldClim 2.1 (Fick and Hijmans 2017, Int. J. Climatol. 37:4302), 10 arc-minute, "
                  "1970-2000 climatology, https://worldclim.org/data/worldclim21.html")
RASTER = "sim.geography.layer_build.layers_raster:"
VECTOR = "sim.geography.layer_build.layers_vector:"


def _natural_earth(product, loader, text_suffix, files=None):
    return Source("Natural Earth " + product, "Natural Earth", "Natural Earth, naturalearthdata.com",
                  "https://www.naturalearthdata.com", NATURAL_EARTH_TERMS, loader,
                  NATURAL_EARTH_TEXT + text_suffix if text_suffix is not None else "",
                  files or {"base": NATURAL_EARTH_BASE})


def _natural_earth_shapefile(product, cache_subdirectory, path, shapefile):
    return _natural_earth(product, "", None, {
        "base": NATURAL_EARTH_BASE, "cache_subdirectory": cache_subdirectory,
        "url": "%s/%s" % (NATURAL_EARTH_BASE, path), "shapefile": shapefile})


def _worldclim(variable, loader, text_suffix):
    return Source(
        "WorldClim 2.1 " + variable, "WorldClim",
        "Fick and Hijmans 2017, Int. J. Climatol. 37:4302", "https://worldclim.org/data/worldclim21.html",
        "non-commercial use; redistribution needs permission", RASTER + loader, WORLDCLIM_TEXT + text_suffix,
        {"base": WORLDCLIM_BASE})


def _worldclim_elevation(loader):
    return _worldclim("elevation (SRTM-derived)", loader, ", elevation (SRTM-derived)")


TREE_COVER_URL = "https://geodata.ucdavis.edu/geodata/landuse/WorldCover_trees_30s.tif"
VGPM_URL = "https://orca.science.oregonstate.edu/data/2x4/monthly/vgpm.r2022.m.chl.m.sst/hdf"

# layer id -> {option name: Source}
SOURCES = {
    "land_mask": {"natural_earth_50m_land": _natural_earth_shapefile(
        "1:50m land", "land", "50m/physical/ne_50m_land.zip", "ne_50m_land.shp")},
    "country_majority": {"natural_earth_50m_admin0": _natural_earth_shapefile(
        "1:50m admin-0 countries", "countries", "50m/cultural/ne_50m_admin_0_countries.zip",
        "ne_50m_admin_0_countries.shp")},
    "koppen_class": {"kgcpy_rubel_2016": Source(
        "Koppen-Geiger present-day map (Rubel et al. 2016, 100 arc-second) bundled in the kgcpy package",
        "Rubel and colleagues, Vienna (maps); kgcpy package",
        "Rubel, Brugger, Haslinger and Auer 2016; Kottek et al. 2006",
        "http://koeppen-geiger.vu-wien.ac.at/present.htm",
        "no data terms stated on the data site; package code BSD",
        "sim.geography.koppen_classifiers:kgcpy_rubel_2016", "", {})},
    "mean_temperature_c": {"worldclim_2_1": _worldclim("bio1", "mean_temperature_c", ", variable bio1")},
    "annual_precipitation_mm": {"worldclim_2_1": _worldclim(
        "bio12", "annual_precipitation_mm", ", variable bio12")},
    "coldest_month_temperature_c": {"worldclim_2_1": _worldclim(
        "monthly tavg", "coldest_month_temperature_c", ", monthly tavg")},
    "warmest_month_temperature_c": {"worldclim_2_1": _worldclim(
        "monthly tavg", "warmest_month_temperature_c", ", monthly tavg")},
    "elevation_mean_m": {"worldclim_2_1": _worldclim_elevation("elevation_mean_m")},
    "elevation_std_m": {"worldclim_2_1": _worldclim_elevation("elevation_std_m")},
    "ruggedness_index": {"worldclim_2_1": _worldclim_elevation("ruggedness_index")},
    "forest_fraction": {"esa_worldcover_2020": Source(
        "ESA WorldCover 2020 tree-cover fraction, 30 arc-second, UC Davis geodata mirror",
        "ESA WorldCover consortium",
        "Zanaga et al. 2021; (c) ESA WorldCover project 2020 / Contains modified Copernicus Sentinel data (2020) "
        "processed by ESA WorldCover consortium",
        TREE_COVER_URL, "CC BY 4.0", RASTER + "forest_fraction",
        "ESA WorldCover 2020 tree-cover fraction at 30 arc-seconds as redistributed by geodata "
        "(%s); Zanaga et al. 2021" % TREE_COVER_URL, {"tree_cover": TREE_COVER_URL})},
    "ocean_productivity_gc_m2_yr": {"oregon_state_vgpm_modis_2022": Source(
        "Oregon State VGPM ocean net primary productivity, MODIS r2022 monthly, 2022", "Oregon State University",
        "Behrenfeld and Falkowski 1997", "http://sites.science.oregonstate.edu/ocean.productivity",
        "no terms found", "sim.geography.layer_build.layers_ocean:ocean_productivity_gc_m2_yr",
        "Oregon State VGPM (Behrenfeld and Falkowski 1997), MODIS r2022 monthly, 2022, "
        "http://sites.science.oregonstate.edu/ocean.productivity", {"monthly_archive": VGPM_URL, "base": NATURAL_EARTH_BASE})},  # base: shelf zone vectors
    "coast_km": {"natural_earth_10m_coastline": _natural_earth(
        "1:10m coastline", VECTOR + "coast_km", " (coastline)")},
    "river_km_all": {"natural_earth_10m_rivers": _natural_earth(
        "1:10m rivers_lake_centerlines", VECTOR + "river_km_all", " (rivers_lake_centerlines)")},
    "river_km_navigable": {"natural_earth_10m_rivers": _natural_earth(
        "1:10m rivers_lake_centerlines", VECTOR + "river_km_navigable", " (rivers_lake_centerlines)")},
    "lake_area_km2": {"natural_earth_10m_lakes": _natural_earth(
        "1:10m lakes", VECTOR + "lake_area_km2", " (lakes)")},
    "shelf_area_km2": {"natural_earth_10m_bathymetry": _natural_earth(
        "1:10m bathymetry L_0 and K_200", "sim.geography.layer_build.layers_shelf:shelf_area_km2", " (bathymetry_L_0, bathymetry_K_200)")},
    "is_port": {"natural_earth_ocean": _natural_earth(
        "1:10m ocean", "sim.geography.layer_build.sea_links:is_port", " (ocean)")},
    "sea_links": {"natural_earth_ocean": _natural_earth(
        "ocean, coastline and admin-0", "sim.geography.layer_build.sea_links:network", None)},
}

# Written into tile_grid.json by tools/generate_geography_tiles.py; every other layer is written by
# sim.geography.layer_build into layers/ (sea_links into sea_links/).
TILE_GRID_LAYERS = ("land_mask", "country_majority", "koppen_class")


def default_option(layer):
    return next(iter(SOURCES[layer]))


def resolve_sources(overrides=()):
    """Option chosen per layer: defaults, replaced by 'layer=option' strings. Unknown names raise ValueError."""
    chosen = {layer: default_option(layer) for layer in SOURCES}
    for override in overrides:
        layer, _, option = override.partition("=")
        if layer not in SOURCES:
            raise ValueError("unknown layer %r; known: %s" % (layer, ", ".join(sorted(SOURCES))))
        if option not in SOURCES[layer]:
            raise ValueError("layer %r has no source option %r; known: %s"
                             % (layer, option, ", ".join(SOURCES[layer])))
        chosen[layer] = option
    return chosen


def loader_of(source):
    """The function a source's `loader` names."""
    module_name, _, function_name = source.loader.partition(":")
    return getattr(importlib.import_module(module_name), function_name)
