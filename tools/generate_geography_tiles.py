#!/usr/bin/env python3
"""Generate data/world/geography.json's "land_tiles" section: the world's
land surface cut into tiles of a fixed, roughly-150,000-km2 size, each
tile's arable fraction and fertility derived from its real climate class,
plus which tiles touch the sea and which tiles border which.

WHY THIS EXISTS. Complaints/46 ("regions are not a unit of area") measured
that data/world/geography.json's 21 hand-drawn regions range from 230,000
km2 (britannia) to 19,800,000 km2 (americas_north) - an 86x spread that has
nothing to do with land scarcity and everything to do with where somebody
drew a border. The stakeholder's own fix: make a region a FIXED quantity of
land (about 150,000 km2), generated programmatically from real geographic
data rather than hand-written, so Rome's own seven regions come out to
about 63 tiles (9.5 million km2 / 150,000) and genuinely have a shape.

THE GENERATING RULE IS THE DELIVERABLE, NOT THE TILES (Complaints/46's own
words). Every number below is produced by applying ONE of the following
rules uniformly, never by looking at a tile and deciding what feels right
for it (CLAUDE.md SS3.1):

  1. GEOMETRY. Project the world into an equal-area coordinate system
     (EPSG:6933, World Cylindrical Equal Area) and lay a regular square
     grid over it, cell side length sqrt(150,000 km2) = ~387.3 km, so every
     interior cell is EXACTLY 150,000 km2 by construction - not "roughly",
     the stakeholder's own number applied literally. A tile's actual
     reported land_area_km2 is smaller than that nominal figure wherever a
     coastline crosses the cell, because it is the REAL area of the land
     inside the cell, not the nominal cell area.
  2. LAND MASK. Intersect every grid cell against Natural Earth's public-
     domain 1:50m land polygons. A cell with less than 10% of its nominal
     area covered by land is dropped entirely - "ocean is not worth
     modelling" (the task's own words) applied down to the tile level: a
     cell that is 91%+ water contributes a sliver of coastline and nothing
     else, and is not worth a tile of its own.
  3. ANTARCTICA. Tiles whose majority country (see rule 5) is Antarctica
     are also dropped, for the same reason one level up: no civilization
     this project has ever modelled reaches it, and every one of its
     tiles would score essentially zero arable land and zero fertility
     under rule 6 regardless (it is almost entirely EF ice-cap climate),
     so keeping roughly 130 inert entries would not change anything a
     civilization can do - see the report this script prints for exactly
     how many tiles this removes.
  4. CENTROID. A tile's reported lat/lon is `representative_point()` of
     its OWN CLIPPED LAND geometry, not the geometric centroid of the
     square cell - a plain centroid can land in open water for a bay-
     shaped or archipelago tile, `representative_point()` cannot.
  5. WHICH COUNTRY. A tile's `country_majority` is whichever Natural Earth
     admin-0 country polygon shares the largest intersection area with the
     tile's clipped land - used only for producing a readable id and for
     reporting the old-region mapping below, never for arable_fraction or
     fertility.
  6. ARABLE FRACTION AND FERTILITY. Both come from ONE lookup table,
     KOPPEN_ARABLE_AND_FERTILITY below, keyed by Koppen-Geiger climate
     class, classified by the `kgcpy` package's bundled raster (Beck et al.
     2018's present-day classification, the standard modern Koppen-Geiger
     product - see that package's own citation). This is the actual
     generating rule for the two numbers Complaints/46 is about: a desert
     tile gets a low arable fraction wherever on Earth it is, a
     Mediterranean-climate tile gets fertility 1.0 wherever on Earth it is,
     never region by region. A tile is classified by SAMPLING A REGULAR
     GRID OF POINTS across its own land area (SAMPLES_PER_AXIS^2 points,
     default 25), not by its single centroid: a 150,000-km2 cell can
     straddle real terrain boundaries (the Alps sit inside the same cell as
     lowland Lombardy in one Italy-majority tile, and a single centroid
     sample happened to land above the tree line, scoring the WHOLE tile as
     tundra even though most of its land is not) - see LIMITS below for
     what this still cannot see. Each cell's arable_fraction and fertility
     are the plain average of KOPPEN_ARABLE_AND_FERTILITY's own numbers
     across every sample point that landed on that tile's actual land, an
     area-weighted blend because the sample grid is evenly spaced. The
     single most common class among the samples is kept too, as
     `koppen_class`, for a readable label - it plays no part in the
     arithmetic.
  7. ANCHORS, NOT TUNING. The table's two anchor points are FIXED before
     the rest of the table is filled in, exactly the way italia's own
     fertility is fixed today: Csa (the class Italy's own tiles fall in)
     is defined as 1.0, because that is the ground data/production/
     40_organics.json's own wheat_kg yield already describes (see
     sim/world/land.py's own module docstring for the identical anchor);
     ET (tundra) is set to 0.05, EXACTLY sim/world/agriculture.py's own
     ARCTIC_TUNDRA quality multiplier, not a coincidentally close number.
     Every other class is filled in relative to those two, by ordinary
     agronomic reasoning (a rainforest's canopy leaches its soil even
     though it never lacks rain; a steppe has thin soil but is not desert;
     a floodplain-fed desert oasis is not modelled as such - see LIMITS
     below), the same reasoning already used, region by region, when this
     project's 21 hand-written regions were written. The difference is
     that this file states the reasoning ONCE, as a table, and applies it
     by rule instead of by 21 separate paragraphs.
  8. BORDERS. Two tiles border each other if and only if they are edge-
     adjacent (not merely corner-touching) in the SAME regular grid rule 1
     built - i.e. one of (row-1,col), (row+1,col), (row,col-1), (row,col+1)
     is also a kept tile. This is the "cheap neighbour lookup" the task
     asks for: an O(1) dict lookup, the same property an H3 or S2 discrete
     global grid would give (see WHY A CUSTOM GRID, NOT H3/S2 below for why
     this script uses a square grid instead of one of those).
  9. SEA ACCESS. A tile is `coastal` if either (a) its own clipped land
     covers less than 98% of the nominal cell area, i.e. part of the cell
     itself is open water, or (b) any of its four rule-8 grid neighbours
     was dropped by rule 2 or 3, i.e. the adjacent ground is mostly ocean
     or ice-continent rather than another land tile. Both conditions are
     evaluated the same way for every tile; there is no per-tile judgement
     call about "is this coastal enough".

WHY A CUSTOM GRID, NOT H3 OR S2. Both were considered, as the task asks.
H3's cells are hexagons of FIXED resolution-defined area that does not sit
at 150,000 km2 at any resolution: resolution 1 averages ~609,800 km2 (Rome
would come out to about 15 tiles, not 63), resolution 2 averages ~86,800
km2 (Rome would come out to about 110). Neither reproduces the stakeholder's
own arithmetic ("9.5 million / 150 thousand"), which is the one number this
whole task is anchored to, and H3/S2's genuine advantages - uniform area,
O(1) neighbour lookup - are both fully available from an equal-area
projected square grid too (rule 1 gives uniform area by construction, rule
8 gives O(1) neighbours), at the cost of hexagons' slightly better isotropy,
which nothing in this project's land-rent or conquest mechanics currently
needs. If a future pass DOES need genuine isotropy (e.g. a diffusion-style
spread mechanic where "distance" in grid steps should not depend on
direction), switching the geometry backend in GRID_AND_LAND_MASK to H3
resolution 2 cells is a small, self-contained change - every other rule
(land mask, centroid, country majority, Koppen lookup, borders via H3's own
`grid_disk`, sea access) carries over unchanged.

LIBRARIES AND DATA, AND WHY. `shapely` and `geopandas` do the geometry
(intersection, area, representative point, spatial join) - both installed
cleanly via pip through this environment's proxy. `kgcpy` supplies the
Koppen-Geiger classification from a bundled raster rather than requiring a
separate multi-hundred-megabyte climate download - also installed cleanly.
Natural Earth's 1:50m physical land polygons and 1:50m cultural country
polygons are public domain and small (about 1.3 MB total); this script
downloads them into a LOCAL CACHE DIRECTORY (default outside the repository
- see CACHE_DIR below) rather than committing them, per the task's own
"if the source data is large, do not commit the raw data" instruction (it
is not large, but the same discipline keeps the repository from
accumulating binary geodata either way). Re-running this script re-
downloads only if the cache is empty; the same two files, byte for byte,
reproduce the same tiles, because every other input (kgcpy's bundled
raster, the code below) is pinned by `pip install` versions - see
REQUIREMENTS below.

REQUIREMENTS (what this was built and tested against):
    pip install shapely==2.1.2 geopandas==1.1.4 kgcpy==1.1.8
Newer compatible versions should work; a materially different Natural
Earth release or kgcpy raster version will shift tile boundaries and
climate calls slightly, which is expected of "generated from real data"
rather than a fixed table, and is exactly why this script - not a
one-off JSON dump - is what is committed.

WHAT THIS SCRIPT DELIBERATELY DOES NOT DO, AND WHY (CLAUDE.md SS3.4: label
every heuristic you cannot yet derive).

  - NO ALLUVIAL/FLOODPLAIN EXCEPTION. The Nile Delta, the Indus and Ganges
    plains, the Yellow River loess belt and the Mississippi bottomlands are
    all historically exceptional farmland sitting inside a Koppen class
    (often BWh desert, for the Nile) that this table otherwise scores low.
    The hand-written geography.json this script's output sits alongside
    modelled this explicitly (north_africa's fertility is 1.35 specifically
    BECAUSE its arable sliver is Nile silt); a pure climate classification
    cannot see a river at all. Fixing this needs a soil dataset (e.g. the
    Harmonized World Soil Database) or an explicit major-river floodplain
    buffer, layered in as a SECOND rule alongside Koppen class, not
    invented per tile. Reported as a named finding below, not patched by
    hand for the tiles that happen to be famous.
  - NO VOLCANIC-SOIL EXCEPTION. Java, the Valley of Mexico and the Ethiopian
    highlands are exceptionally fertile on volcanic soil the hand-written
    file calls out by name; Koppen class cannot see geology either. Same
    fix, same reason not attempted here.
  - NO ANTIMERIDIAN WRAPAROUND. Rule 8's grid is a flat row/col plane; the
    handful of tiles that would border across +/-180 degrees longitude
    (eastern Russia/Alaska, Fiji) are not linked as neighbours. Affects a
    handful of tiles out of about a thousand; noted, not fixed, because
    doing it right means carrying the grid's own column count and wrapping
    modulo it, which is a small but real change this script does not make
    to keep the adjacency rule the same one sentence for every tile.
  - NO WIRING INTO sim/world/land.py, sim/solve_prices.py OR
    data/civilizations/*.json. Those files are out of this task's
    ownership (another agent is concurrently adding land.py's own
    intensive margin) and Complaints/46 itself recommends re-tiling as
    "its own deliberate pass" separate from that work. This script adds
    its output as data/world/geography.json's own NEW "land_tiles" key,
    alongside the existing "regions" key, which is left untouched - see
    that key's own "_doc" field once written for the mapping from old
    region to new tiles and exactly what a later pass would need to change
    in sim/world/land.py and data/civilizations/*.json to read tiles
    instead of regions.

USAGE:
    python3 tools/generate_geography_tiles.py
    python3 tools/generate_geography_tiles.py --cache-dir /some/dir --out data/world/geography.json
    python3 tools/generate_geography_tiles.py --report-only   # print stats, write nothing

Runtime: under 15 seconds end to end on this environment, most of it spent
building the land mask (see the timing this script itself prints).
"""
import argparse
import collections
import json
import math
import os
import sys
import time
import zipfile
import io
import urllib.request
import ssl

# ============================================================================
# CACHE AND DOWNLOAD - Natural Earth's public-domain vector layers, fetched
# once into a cache directory OUTSIDE the repository, never committed.
# ============================================================================

DEFAULT_CACHE_DIR = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
    "bootstrap_history_geography_tiles")

NATURAL_EARTH_BASE_URL = "https://naciscdn.org/naturalearth"

# (cache subdirectory, download url, expected shapefile basename)
NATURAL_EARTH_LAYERS = {
    "land": (
        "land",
        f"{NATURAL_EARTH_BASE_URL}/50m/physical/ne_50m_land.zip",
        "ne_50m_land.shp",
    ),
    "countries": (
        "countries",
        f"{NATURAL_EARTH_BASE_URL}/50m/cultural/ne_50m_admin_0_countries.zip",
        "ne_50m_admin_0_countries.shp",
    ),
}


def _download_and_extract(url, destination_directory):
    os.makedirs(destination_directory, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "bootstrap-history-geography-tiles/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        archive.extractall(destination_directory)


def ensure_natural_earth_layer(layer_key, cache_dir):
    """Returns the local .shp path for `layer_key`, downloading into
    `cache_dir` first if it is not already there. Idempotent: a second
    call with the same cache_dir does no network access at all.
    """
    subdirectory, url, shapefile_name = NATURAL_EARTH_LAYERS[layer_key]
    layer_dir = os.path.join(cache_dir, subdirectory)
    shapefile_path = os.path.join(layer_dir, shapefile_name)
    if not os.path.exists(shapefile_path):
        print("  downloading %s ..." % url)
        _download_and_extract(url, layer_dir)
    return shapefile_path


# ============================================================================
# THE GRID - rule 1. One cell is EXACTLY this many square kilometres in the
# equal-area projection, by construction.
# ============================================================================

TARGET_TILE_AREA_KM2 = 150000.0
EQUAL_AREA_CRS = 6933  # EPSG:6933, WGS 84 / NSIDC EASE-Grid 2.0 Global
MINIMUM_LAND_FRACTION_TO_KEEP_A_TILE = 0.10  # rule 2
OWN_CELL_COASTAL_LAND_FRACTION = 0.98        # rule 9(a)
CLIMATE_SAMPLES_PER_AXIS = 5   # rule 6: a 5x5 = 25-point grid per tile,
                               # not one centroid - see the module
                               # docstring's rule 6 for why


# ============================================================================
# THE CLIMATE TABLE - rule 6/7. ONE table, applied by lookup, never by
# looking at where a tile happens to be.
#
# Values are (arable_fraction, fertility_quality_multiplier). Both are
# engineering estimates in the same sense every non-italia region in the
# existing geography.json is one (confidence D): the DIRECTION each one
# encodes is well attested agronomically, the exact SIZE is a placeholder
# pending a real soil survey, exactly the discipline sim/world/land.py's
# own module docstring already states for the hand-written file this
# table's own output sits alongside.
#
#   Csa is fixed at fertility 1.0: this is the class Italy's own tiles
#       fall in, and data/production/40_organics.json's wheat_kg entry IS
#       Roman-Italian dry-farmed wheat - the SAME anchor the hand-written
#       geography.json already uses, reached here by climate class instead
#       of by name.
#   ET is fixed at fertility 0.05: sim/world/agriculture.py's own
#       ARCTIC_TUNDRA quality multiplier, reused exactly rather than
#       independently re-estimated, because the two describe the same
#       physical ground (growing-season length, not soil, is what limits
#       tundra) - see that module's own note on this figure.
#   EF (permanent ice) is 0.0 arable, 0.0 fertility: nothing grows on an
#       ice sheet regardless of what "fertility" a soil survey there would
#       even mean.
# Every other row is ordinary agronomic reasoning: a hot desert's arable
# share is whatever oases and the rare river give it (see LIMITS in the
# module docstring for why river silt itself is not modelled); a tropical
# rainforest is never short of rain but its canopy leaches the soil below
# it; a humid subtropical class with no dry season and a hot summer (the
# Yangtze basin's own class) is given fertility slightly ABOVE the
# Mediterranean anchor for the same reason data/world/geography.json's own
# china entry already gives China's arable sliver 1.3: this is rice
# country, and rice yields more calories per hectare than wheat under
# comparable technology, well attested agronomically and independent of
# any per-region judgement about China specifically.
# ============================================================================

KOPPEN_ARABLE_AND_FERTILITY = {
    # ---- A: tropical -------------------------------------------------
    "Af": (0.15, 0.65),  # rainforest, no dry season: canopy limits clearing, leaches soil
    "Am": (0.30, 0.90),  # monsoon: a real dry season aids clearing; rice country
    "Aw": (0.30, 0.75),  # savanna, dry winter: workable but thinner, erodible soils
    "As": (0.30, 0.75),  # savanna, dry summer: same treatment as Aw
    # ---- B: arid -------------------------------------------------------
    "BWh": (0.02, 0.55),  # hot desert: almost nothing arable outside oases (see LIMITS)
    "BWk": (0.02, 0.45),  # cold desert: same, shorter growing season where anything grows
    "BSh": (0.20, 0.60),  # hot semi-arid steppe: dryland grain, thin soils
    "BSk": (0.22, 0.55),  # cold semi-arid steppe: same, cooler
    # ---- C: temperate ----------------------------------------------------
    "Csa": (0.35, 1.00),  # Mediterranean, hot summer - THE ANCHOR (Italy's own class)
    "Csb": (0.32, 0.95),  # Mediterranean, warm summer: cooler/wetter than Csa
    "Csc": (0.25, 0.85),  # Mediterranean, cold summer: rare, montane
    "Cwa": (0.32, 0.95),  # dry-winter subtropical, hot summer: monsoon-adjacent, good grain land
    "Cwb": (0.28, 0.85),  # dry-winter subtropical, warm summer: highland version of the above
    "Cwc": (0.20, 0.70),  # dry-winter subtropical, cold summer: montane, marginal
    "Cfa": (0.35, 1.05),  # humid subtropical, no dry season: the Yangtze basin's own class, rice country
    "Cfb": (0.30, 0.90),  # oceanic: Britain and Gaul's own class, temperate lowland
    "Cfc": (0.22, 0.75),  # subpolar oceanic: short cool summer
    # ---- D: continental --------------------------------------------------
    "Dsa": (0.28, 0.80), "Dsb": (0.24, 0.75), "Dsc": (0.10, 0.55), "Dsd": (0.08, 0.50),
    "Dwa": (0.28, 0.85), "Dwb": (0.24, 0.80), "Dwc": (0.10, 0.55), "Dwd": (0.06, 0.45),
    "Dfa": (0.30, 0.90), "Dfb": (0.26, 0.85), "Dfc": (0.08, 0.45), "Dfd": (0.04, 0.35),
    # ---- E: polar ----------------------------------------------------------
    "ET": (0.005, 0.05),  # tundra - matches sim/world/agriculture.py's ARCTIC_TUNDRA exactly
    "EF": (0.0, 0.0),     # permanent ice
}


# ============================================================================
# OLD REGION MAPPING - for the report only, never for a tile's own numbers.
# Each of the 21 hand-written geography.json regions names, in its own
# `land.source` text, roughly which modern countries it groups (and its own
# stated land_area_km2 is close to summing exactly those countries' real
# areas - checked by hand while building this map, see the report this
# script prints). Used ONLY to answer "what would have to change in
# data/civilizations/*.json" - it plays no part in any tile's geometry,
# arable fraction or fertility, which come from rules 1-9 above regardless
# of which old region (if any) a tile's ground used to be filed under.
# A country left out of every list below is a country the OLD 21-region
# file never covered at all - see the report's "gaps in the old scheme"
# section, itself a finding, not something this script invents a fix for.
# ============================================================================

COUNTRY_TO_OLD_REGION = {
    "Italy": "italia", "Vatican": "italia", "San Marino": "italia",
    "France": "gaul_germania", "Germany": "gaul_germania",
    "Netherlands": "gaul_germania", "Belgium": "gaul_germania",
    "Luxembourg": "gaul_germania",
    "United Kingdom": "britannia",
    "Spain": "hispania", "Portugal": "hispania",
    "Morocco": "north_africa", "Algeria": "north_africa",
    "Tunisia": "north_africa", "Libya": "north_africa", "Egypt": "north_africa",
    "Greece": "greece_anatolia", "Turkey": "greece_anatolia",
    "Syria": "levant_mesopotamia", "Iraq": "levant_mesopotamia",
    "Lebanon": "levant_mesopotamia", "Jordan": "levant_mesopotamia",
    "Israel": "levant_mesopotamia", "Palestine": "levant_mesopotamia",
    "Sweden": "scandinavia", "Norway": "scandinavia",
    "Denmark": "scandinavia", "Finland": "scandinavia",
    "Saudi Arabia": "arabia_horn", "Yemen": "arabia_horn", "Oman": "arabia_horn",
    "United Arab Emirates": "arabia_horn", "Qatar": "arabia_horn",
    "Kuwait": "arabia_horn", "Bahrain": "arabia_horn",
    "Ethiopia": "arabia_horn", "Eritrea": "arabia_horn", "Somalia": "arabia_horn",
    "Somaliland": "arabia_horn", "Djibouti": "arabia_horn",
    "India": "india", "Sri Lanka": "india",
    "Iran": "persia_centralasia", "Afghanistan": "persia_centralasia",
    "Turkmenistan": "persia_centralasia", "Uzbekistan": "persia_centralasia",
    "Tajikistan": "persia_centralasia", "Kyrgyzstan": "persia_centralasia",
    "China": "china", "Taiwan": "china", "Hong Kong": "china", "Macao": "china",
    "Nigeria": "west_africa", "Ghana": "west_africa", "Côte d'Ivoire": "west_africa",
    "Senegal": "west_africa", "Mali": "west_africa", "Cameroon": "west_africa",
    "Dem. Rep. Congo": "west_africa", "Guinea": "west_africa",
    "Sierra Leone": "west_africa", "Liberia": "west_africa",
    "Burkina Faso": "west_africa", "Togo": "west_africa", "Benin": "west_africa",
    "Guinea-Bissau": "west_africa", "Gambia": "west_africa",
    "Central African Rep.": "west_africa", "Congo": "west_africa",
    "Gabon": "west_africa", "Eq. Guinea": "west_africa",
    "Indonesia": "southeast_asia", "Malaysia": "southeast_asia",
    "South Africa": "east_africa_south", "Zimbabwe": "east_africa_south",
    "Zambia": "east_africa_south", "Mozambique": "east_africa_south",
    "Tanzania": "east_africa_south", "Kenya": "east_africa_south",
    "eSwatini": "east_africa_south", "Lesotho": "east_africa_south",
    # siberia_urals is Russia EAST of the Urals only - see split_russia_by_urals()
    "Mexico": "americas_carib", "Belize": "americas_carib",
    "Guatemala": "americas_carib", "Honduras": "americas_carib",
    "El Salvador": "americas_carib", "Nicaragua": "americas_carib",
    "Costa Rica": "americas_carib", "Panama": "americas_carib",
    "Cuba": "americas_carib", "Haiti": "americas_carib",
    "Dominican Rep.": "americas_carib", "Jamaica": "americas_carib",
    "Bahamas": "americas_carib", "Puerto Rico": "americas_carib",
    "Trinidad and Tobago": "americas_carib",
    "Brazil": "americas_south", "Argentina": "americas_south",
    "Chile": "americas_south", "Peru": "americas_south",
    "Colombia": "americas_south", "Venezuela": "americas_south",
    "Ecuador": "americas_south", "Bolivia": "americas_south",
    "Paraguay": "americas_south", "Uruguay": "americas_south",
    "Guyana": "americas_south", "Suriname": "americas_south",
    "United States of America": "americas_north", "Canada": "americas_north",
    "Australia": "australia_pacific", "New Zealand": "australia_pacific",
    "Papua New Guinea": "australia_pacific", "Fiji": "australia_pacific",
    "Solomon Is.": "australia_pacific", "Vanuatu": "australia_pacific",
    "New Caledonia": "australia_pacific",
    "Greenland": "greenland_arctic",
    # Antarctica is dropped outright (rule 3), so it needs no entry here.
}

URALS_SPLIT_LONGITUDE_DEGREES = 60.0  # rule for splitting Russia's own
                                      # polygon into "siberia_urals" (east
                                      # of this meridian) and unmapped
                                      # European Russia (west of it) - see
                                      # the report's own note on this gap.


def old_region_for_tile(country_majority, lon):
    if country_majority == "Russia":
        return "siberia_urals" if lon >= URALS_SPLIT_LONGITUDE_DEGREES else None
    return COUNTRY_TO_OLD_REGION.get(country_majority)


# ============================================================================
# TILE ID - rule: deterministic slug + a zero-padded sequence number,
# assigned in a fixed (country, row, col) sort order so the SAME input data
# always produces the SAME ids, run to run.
# ============================================================================

def slugify(name):
    keep = []
    for character in name.lower():
        if character.isalnum():
            keep.append(character)
        elif keep and keep[-1] != "_":
            keep.append("_")
    return "".join(keep).strip("_") or "unknown"


def assign_tile_ids(tiles):
    """tiles: list of dict with at least 'country_majority', 'row', 'col'.
    Adds 'id' to each dict in place, and returns the same list, ordered by
    id for a stable, readable file.
    """
    by_country = {}
    for tile in tiles:
        by_country.setdefault(tile["country_majority"] or "unclaimed", []).append(tile)
    for country, group in by_country.items():
        group.sort(key=lambda t: (t["row"], t["col"]))
        width = max(2, len(str(len(group))))
        slug = slugify(country)
        for index, tile in enumerate(group, start=1):
            tile["id"] = "%s_%s" % (slug, str(index).zfill(width))
    tiles.sort(key=lambda t: t["id"])
    return tiles


# ============================================================================
# THE MAIN PIPELINE
# ============================================================================

def build_tiles(cache_dir, verbose=True):
    import geopandas
    import shapely
    from shapely.geometry import box
    import kgcpy

    def log(message):
        if verbose:
            print(message)

    start = time.time()
    land_shapefile = ensure_natural_earth_layer("land", cache_dir)
    countries_shapefile = ensure_natural_earth_layer("countries", cache_dir)

    land = geopandas.read_file(land_shapefile).to_crs(EQUAL_AREA_CRS)
    countries = geopandas.read_file(countries_shapefile)
    countries_equal_area = countries.to_crs(EQUAL_AREA_CRS)
    land_union = shapely.unary_union(land.geometry.values)
    log("  loaded and unioned Natural Earth land polygons in %.2fs" % (time.time() - start))

    cell_side_metres = math.sqrt(TARGET_TILE_AREA_KM2) * 1000.0
    min_x, min_y, max_x, max_y = land_union.bounds
    first_col = math.floor(min_x / cell_side_metres) - 1
    last_col = math.ceil(max_x / cell_side_metres) + 1
    first_row = math.floor(min_y / cell_side_metres) - 1
    last_row = math.ceil(max_y / cell_side_metres) + 1

    stage_start = time.time()
    kept_by_row_col = {}
    for row in range(first_row, last_row):
        cell_y0 = row * cell_side_metres
        cell_y1 = cell_y0 + cell_side_metres
        for col in range(first_col, last_col):
            cell_x0 = col * cell_side_metres
            cell_x1 = cell_x0 + cell_side_metres
            cell = box(cell_x0, cell_y0, cell_x1, cell_y1)
            if not shapely.intersects(land_union, cell):
                continue
            clipped_land = shapely.intersection(land_union, cell)
            land_area_km2 = shapely.area(clipped_land) / 1e6
            if land_area_km2 / TARGET_TILE_AREA_KM2 < MINIMUM_LAND_FRACTION_TO_KEEP_A_TILE:
                continue  # rule 2: this cell is almost entirely open water
            kept_by_row_col[(row, col)] = {
                "row": row, "col": col,
                "geometry": clipped_land,
                "land_area_km2": land_area_km2,
            }
    log("  built the equal-area grid and land mask in %.2fs (%d candidate land cells)"
        % (time.time() - stage_start, len(kept_by_row_col)))

    tiles = list(kept_by_row_col.values())
    tiles_gdf = geopandas.GeoDataFrame(tiles, crs=EQUAL_AREA_CRS)

    # rule 4: representative point, not a plain centroid
    stage_start = time.time()
    representative_points = tiles_gdf.geometry.representative_point()
    points_lonlat = representative_points.to_crs(4326)
    for tile, point in zip(tiles, points_lonlat):
        tile["lon"] = point.x
        tile["lat"] = point.y
    log("  computed representative points in %.2fs" % (time.time() - stage_start))

    # rule 5: majority country by intersection area, via a spatial join to
    # cut candidates down before the (more expensive) exact-area comparison
    stage_start = time.time()
    joined = geopandas.sjoin(
        tiles_gdf[["geometry"]].reset_index().rename(columns={"index": "tile_index"}),
        countries_equal_area[["NAME", "geometry"]],
        how="inner", predicate="intersects")
    country_geometry_by_name = dict(zip(countries_equal_area["NAME"], countries_equal_area.geometry))
    tile_geometry_by_index = dict(zip(tiles_gdf.index, tiles_gdf.geometry))
    best_country_by_tile_index = {}
    for tile_index, group in joined.groupby("tile_index"):
        tile_geometry = tile_geometry_by_index[tile_index]
        best_name, best_area = None, -1.0
        for country_name in group["NAME"]:
            overlap_area = shapely.area(
                shapely.intersection(tile_geometry, country_geometry_by_name[country_name]))
            if overlap_area > best_area:
                best_name, best_area = country_name, overlap_area
        best_country_by_tile_index[tile_index] = best_name
    for tile_index, tile in enumerate(tiles):
        tile["country_majority"] = best_country_by_tile_index.get(tile_index)
    log("  assigned majority country in %.2fs" % (time.time() - stage_start))

    # rule 3: drop Antarctica outright
    before = len(tiles)
    tiles = [tile for tile in tiles if tile["country_majority"] != "Antarctica"]
    log("  dropped %d Antarctica tile(s) (rule 3)" % (before - len(tiles)))
    kept_by_row_col = {(t["row"], t["col"]): t for t in tiles}

    # rule 6/7: climate class and the arable/fertility lookup, sampled
    # across each tile's own land area rather than at one centroid - see
    # the module docstring's rule 6 for why a single point is not enough.
    stage_start = time.time()
    import numpy
    from shapely.geometry import Point

    def classify_koppen(lat, lon):
        # Normalise longitude into [-180, 180) first: a sample point right
        # at the antimeridian can reproject to 180.00000003 or -180.0 -
        # a floating-point artifact of the equal-area round trip, not a
        # real ambiguity - and kgcpy indexes a fixed-width raster by lon,
        # so an out-of-range value throws instead of classifying. This is
        # applied to every sample point everywhere, not just ones this
        # script happened to notice failing (Fiji, which straddles the
        # antimeridian, is what surfaced it).
        lon = ((lon + 180.0) % 360.0) - 180.0
        # kgcpy.lookupCZ can land on a pixel the raster itself calls
        # "Ocean" (its own no-data class), which happens occasionally for
        # a sample point right at a coastline where this script's own land
        # polygon and the raster's do not agree pixel-for-pixel;
        # nearbyCZ's expanding search finds the nearest REAL land
        # classification instead of this script inventing one by hand.
        try:
            climate_zone = kgcpy.lookupCZ(lat, lon)
            if climate_zone != "Ocean":
                return climate_zone
        except Exception:
            pass
        for size in (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144):
            try:
                climate_zone, _uncertainty, nearby = kgcpy.nearbyCZ(lat, lon, size=size)
                if climate_zone != "Ocean":
                    return climate_zone
                real_land_nearby = [zone for zone in nearby if zone != "Ocean"]
                if real_land_nearby:
                    return real_land_nearby[0]
            except Exception:
                continue
        return None

    def sample_points_within(tile_geometry):
        """CLIMATE_SAMPLES_PER_AXIS^2 evenly-spaced points (equal-area CRS)
        that actually fall on `tile_geometry`'s own land - an area sample,
        not a single centroid. Falls back to one representative_point() if
        the tile's land is too thin/scattered for any grid point to land
        on it (rare - a sliver island tile smaller than the sample
        spacing).
        """
        min_x, min_y, max_x, max_y = tile_geometry.bounds
        xs = numpy.linspace(min_x, max_x, CLIMATE_SAMPLES_PER_AXIS + 2)[1:-1]
        ys = numpy.linspace(min_y, max_y, CLIMATE_SAMPLES_PER_AXIS + 2)[1:-1]
        points = [Point(x, y) for x in xs for y in ys]
        inside = [p for p in points if shapely.intersects(tile_geometry, p)]
        return inside if inside else [tile_geometry.representative_point()]

    unclassified_count = 0
    for tile in tiles:
        sample_points = sample_points_within(tile["geometry"])
        sample_points_lonlat = geopandas.GeoSeries(
            sample_points, crs=EQUAL_AREA_CRS).to_crs(4326)
        sample_classes = [classify_koppen(point.y, point.x) for point in sample_points_lonlat]

        arable_fractions, fertilities = [], []
        for koppen_class in sample_classes:
            looked_up = KOPPEN_ARABLE_AND_FERTILITY.get(koppen_class)
            if looked_up is None:
                unclassified_count += 1
                # Only reachable if kgcpy's own raster returns a class this
                # table does not list (it lists every standard Koppen-Geiger
                # class kgcpy can produce) - fails loudly rather than
                # silently inventing a number, per CLAUDE.md SS3.1.
                raise ValueError(
                    "tile %r sample classified as %r, which is not in "
                    "KOPPEN_ARABLE_AND_FERTILITY" % (tile.get("country_majority"), koppen_class))
            arable_fractions.append(looked_up[0])
            fertilities.append(looked_up[1])

        tile["koppen_class"] = collections.Counter(sample_classes).most_common(1)[0][0]
        tile["koppen_sample_mix"] = dict(collections.Counter(sample_classes))
        tile["arable_fraction"] = sum(arable_fractions) / len(arable_fractions)
        tile["fertility_quality_multiplier"] = sum(fertilities) / len(fertilities)
    log("  classified climate (%d samples/tile) and looked up arable/fertility "
        "for %d tiles in %.2fs"
        % (CLIMATE_SAMPLES_PER_AXIS ** 2, len(tiles), time.time() - stage_start))

    # rule 8/9: borders and sea access, from grid adjacency alone
    for tile in tiles:
        row, col = tile["row"], tile["col"]
        neighbour_keys = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        neighbours_present = [kept_by_row_col[key] for key in neighbour_keys if key in kept_by_row_col]
        tile["_neighbour_keys"] = neighbour_keys
        own_cell_touches_water = (
            tile["land_area_km2"] / TARGET_TILE_AREA_KM2 < OWN_CELL_COASTAL_LAND_FRACTION)
        missing_a_neighbour = len(neighbours_present) < len(neighbour_keys)
        tile["coastal"] = bool(own_cell_touches_water or missing_a_neighbour)

    # rule: old-region mapping, for the report/migration path only
    for tile in tiles:
        tile["old_region"] = old_region_for_tile(tile["country_majority"], tile["lon"])

    # ids, assigned last so every other field is final first
    assign_tile_ids(tiles)
    id_by_row_col = {(t["row"], t["col"]): t["id"] for t in tiles}
    for tile in tiles:
        tile["borders"] = sorted(
            id_by_row_col[key] for key in tile["_neighbour_keys"] if key in id_by_row_col)
        del tile["_neighbour_keys"]
        del tile["geometry"]  # not JSON-serialisable and not part of the output schema
        del tile["row"]
        del tile["col"]

    log("  total pipeline time %.2fs" % (time.time() - start))
    return tiles


# ============================================================================
# OUTPUT - written under geography.json's own NEW "land_tiles" key, next to
# (not instead of) the existing "regions" key - see the module docstring's
# WHAT THIS SCRIPT DELIBERATELY DOES NOT DO section for why.
# ============================================================================

def build_land_tiles_section(tiles):
    tiles_by_id = {}
    for tile in tiles:
        tile_id = tile.pop("id")
        tile_record = {
            "lat": round(tile["lat"], 4),
            "lon": round(tile["lon"], 4),
            "land_area_km2": round(tile["land_area_km2"], 1),
            "arable_fraction": round(tile["arable_fraction"], 4),
            "fertility_quality_multiplier": round(tile["fertility_quality_multiplier"], 4),
            "coastal": tile["coastal"],
            "borders": tile["borders"],
            "conf": "D",
            "koppen_class": tile["koppen_class"],
            "koppen_sample_mix": tile["koppen_sample_mix"],
            "country_majority": tile["country_majority"],
            "old_region": tile["old_region"],
            "source": (
                "Generated by tools/generate_geography_tiles.py: an equal-area "
                "%.0f-km2 grid cell (rule 1), clipped to Natural Earth 1:50m land "
                "(rule 2), classified %s by Koppen-Geiger climate (rule 6) via the "
                "kgcpy package, arable_fraction and fertility_quality_multiplier "
                "read off that class from KOPPEN_ARABLE_AND_FERTILITY - never "
                "estimated for this tile individually."
                % (TARGET_TILE_AREA_KM2, tile["koppen_class"])),
        }
        tiles_by_id[tile_id] = tile_record

    region_to_tiles = {}
    unmapped_tile_count = 0
    for tile_id, record in tiles_by_id.items():
        region = record["old_region"]
        if region is None:
            unmapped_tile_count += 1
            continue
        region_to_tiles.setdefault(region, []).append(tile_id)
    for region in region_to_tiles:
        region_to_tiles[region].sort()

    return {
        "_doc": (
            "Generated by tools/generate_geography_tiles.py - re-run that script "
            "to reproduce or refresh this section; do not hand-edit it. See its "
            "own module docstring for the numbered generating rule this section "
            "is the OUTPUT of (Complaints/46: 'the generating rule is the "
            "deliverable, not the tiles'). Each tile is a roughly-%.0f-km2 "
            "piece of real land (smaller at a coastline, per rule 1/2), never "
            "hand-judged. This key sits ALONGSIDE the file's existing `regions` "
            "key, which this script does not touch: sim/world/land.py and "
            "sim/engine/economy.py (both out of this task's ownership) still "
            "read `regions`/`home_regions` exactly as before, and every civ file "
            "still works unmodified. `region_to_tiles` below is the mapping a "
            "later pass would use to move data/civilizations/*.json's own "
            "`home_regions` from old region ids onto lists of these tile ids - "
            "see this task's own report for exactly what that change would be "
            "and why it is not made here."
        ),
        "generation_rule_summary": (
            "Equal-area %.0f km2 grid cells (EPSG:6933) intersected with "
            "Natural Earth 1:50m land; cells under 10%% land dropped; "
            "Antarctica dropped outright; each tile's arable_fraction and "
            "fertility_quality_multiplier read from ONE table keyed by its "
            "centroid's Koppen-Geiger climate class, anchored at Csa=1.0 "
            "(Italy's own class, matching data/production/40_organics.json's "
            "wheat_kg) and ET=0.05 (matching sim/world/agriculture.py's own "
            "ARCTIC_TUNDRA); borders are grid edge-adjacency; a tile is "
            "coastal if part of its own cell is water or a grid neighbour "
            "was dropped." % TARGET_TILE_AREA_KM2
        ),
        "tile_count": len(tiles_by_id),
        "target_tile_area_km2": TARGET_TILE_AREA_KM2,
        "tiles": dict(sorted(tiles_by_id.items())),
        "region_to_tiles": dict(sorted(region_to_tiles.items())),
        "unmapped_tile_count": unmapped_tile_count,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "world", "geography.json"),
        help="geography.json to update in place (default: the repo's own copy)")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR,
        help="where to cache downloaded Natural Earth shapefiles (default: %s)"
             % DEFAULT_CACHE_DIR)
    parser.add_argument("--report-only", action="store_true",
        help="build the tiles and print the summary report, but write nothing")
    arguments = parser.parse_args()

    print("Building land tiles (target %.0f km2 each)..." % TARGET_TILE_AREA_KM2)
    tiles = build_tiles(arguments.cache_dir)
    section = build_land_tiles_section(tiles)

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print("tiles: %d" % section["tile_count"])
    print("total land area covered: %.0f km2" % sum(
        t["land_area_km2"] for t in section["tiles"].values()))
    print("tiles with no old-region match (gaps in the 21-region scheme): %d"
          % section["unmapped_tile_count"])
    print()
    print("old region -> tile count, tile-summed area vs hand-written area:")
    geography_path = arguments.out
    old_regions = {}
    if os.path.exists(geography_path):
        with open(geography_path) as handle:
            old_regions = json.load(handle).get("regions", {})
    for region_id, tile_ids in sorted(section["region_to_tiles"].items()):
        tile_area = sum(section["tiles"][tid]["land_area_km2"] for tid in tile_ids)
        old_land = (old_regions.get(region_id) or {}).get("land") or {}
        old_area = old_land.get("land_area_km2")
        old_fert = old_land.get("fertility_quality_multiplier")
        tile_fert_avg = sum(
            section["tiles"][tid]["fertility_quality_multiplier"] * section["tiles"][tid]["land_area_km2"]
            for tid in tile_ids) / tile_area if tile_area else 0.0
        print("  %-20s tiles=%3d  tile_area=%12s  hand_area=%12s  "
              "tile_fert(area-wtd)=%.3f  hand_fert=%s"
              % (region_id, len(tile_ids), format(round(tile_area), ","),
                 format(old_area, ",") if old_area else "-",
                 tile_fert_avg, old_fert if old_fert is not None else "-"))

    if arguments.report_only:
        print("\n--report-only: nothing written.")
        return

    with open(geography_path) as handle:
        geography = json.load(handle)
    geography["land_tiles"] = section
    with open(geography_path, "w") as handle:
        json.dump(geography, handle, indent=1, sort_keys=False)
        handle.write("\n")
    print("\nWrote %d tiles to %s under the new \"land_tiles\" key." % (len(tiles), geography_path))


if __name__ == "__main__":
    main()
