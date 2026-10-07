"""Registry of the dataset behind each generated map layer.

One entry per layer, one option per dataset that can fill it. Swapping a
layer's dataset means adding an option here (and the loader or files it
needs), then naming it with `--source layer=option` on the generator. The
first option of each layer is its default: the dataset the committed files
were built from.
"""
from collections import namedtuple

Source = namedtuple("Source", "dataset provider citation url terms")

NATURAL_EARTH_TERMS = "public domain"
WORLDCLIM_TERMS = "non-commercial use; redistribution needs permission"


def _natural_earth(product):
    return Source("Natural Earth " + product, "Natural Earth", "Natural Earth, naturalearthdata.com",
                  "https://www.naturalearthdata.com", NATURAL_EARTH_TERMS)


def _worldclim(variable):
    return Source(
        "WorldClim 2.1 " + variable, "WorldClim",
        "Fick and Hijmans 2017, Int. J. Climatol. 37:4302", "https://worldclim.org/data/worldclim21.html",
        WORLDCLIM_TERMS)


WORLDCLIM_ELEVATION = _worldclim("elevation (SRTM-derived)")

# layer id -> {option name: Source}
SOURCES = {
    "land_mask": {"natural_earth_50m_land": _natural_earth("1:50m land")},
    "country_majority": {"natural_earth_50m_admin0": _natural_earth("1:50m admin-0 countries")},
    "koppen_class": {"kgcpy_rubel_2016": Source(
        "Koppen-Geiger present-day map (Rubel et al. 2016, 100 arc-second) bundled in the kgcpy package",
        "Rubel and colleagues, Vienna (maps); kgcpy package",
        "Rubel, Brugger, Haslinger and Auer 2016; Kottek et al. 2006",
        "http://koeppen-geiger.vu-wien.ac.at/present.htm",
        "no data terms stated on the data site; package code BSD")},
    "mean_temperature_c": {"worldclim_2_1": _worldclim("bio1")},
    "annual_precipitation_mm": {"worldclim_2_1": _worldclim("bio12")},
    "coldest_month_temperature_c": {"worldclim_2_1": _worldclim("monthly tavg")},
    "warmest_month_temperature_c": {"worldclim_2_1": _worldclim("monthly tavg")},
    "elevation_mean_m": {"worldclim_2_1": WORLDCLIM_ELEVATION},
    "elevation_std_m": {"worldclim_2_1": WORLDCLIM_ELEVATION},
    "ruggedness_index": {"worldclim_2_1": WORLDCLIM_ELEVATION},
    "forest_fraction": {"esa_worldcover_2020": Source(
        "ESA WorldCover 2020 tree-cover fraction, 30 arc-second, UC Davis geodata mirror",
        "ESA WorldCover consortium",
        "Zanaga et al. 2021; (c) ESA WorldCover project 2020 / Contains modified Copernicus Sentinel data (2020) "
        "processed by ESA WorldCover consortium",
        "https://geodata.ucdavis.edu/geodata/landuse/WorldCover_trees_30s.tif", "CC BY 4.0")},
    "ocean_productivity_gc_m2_yr": {"oregon_state_vgpm_modis_2022": Source(
        "Oregon State VGPM ocean net primary productivity, MODIS r2022 monthly, 2022", "Oregon State University",
        "Behrenfeld and Falkowski 1997", "http://sites.science.oregonstate.edu/ocean.productivity",
        "no terms found")},
    "coast_km": {"natural_earth_10m_coastline": _natural_earth("1:10m coastline")},
    "river_km_all": {"natural_earth_10m_rivers": _natural_earth("1:10m rivers_lake_centerlines")},
    "river_km_navigable": {"natural_earth_10m_rivers": _natural_earth("1:10m rivers_lake_centerlines")},
    "lake_area_km2": {"natural_earth_10m_lakes": _natural_earth("1:10m lakes")},
    "shelf_area_km2": {"natural_earth_10m_bathymetry": _natural_earth("1:10m bathymetry L_0 and K_200")},
    "is_port": {"natural_earth_10m_ocean": _natural_earth("1:10m ocean")},
}

# Written by tools/generate_geography_tiles.py into tile_grid.json; every other layer is written by
# sim.geography.layer_build into layers/.
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
