"""Declared numbers the agriculture module owns."""
from sim.constants import declare

FARM_WEATHER_POOLED_CELL_CAP = declare(
    "FARM_WEATHER_POOLED_CELL_CAP", 100,
    kind="temporary_heuristic",
    unit="count (pooled growing-season weather cells per civilisation, an "
         "upper bound independent of land_tiles resolution)",
    source="Not a measured or published figure. Anchored to the largest shipped "
           "civilisation's measured cell count (pinned by "
           "sim/tests/test_growing_season_weather_correlation.py) plus headroom, "
           "not derived from a formula relating cell count to "
           "GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM.",
    confidence="D",
    why="Bounds the O(cell_count**3) one-time Cholesky factorisation and the "
        "O(cell_count**2) per-year matrix-vector product of the pooled harvest "
        "weather to a constant cost however finely land_tiles divides a "
        "civilisation's territory (docs/architecture/MAP_AND_WEATHER.md section 4.2). "
        "At or under the cap nothing changes; above it cells are merged, not "
        "dropped, into cap-many spatially coherent cells weighted by arable area.")

FARM_LABOUR_HOURS_PER_HA = declare(
    "FARM_LABOUR_HOURS_PER_HA", 1500.0, kind="temporary_heuristic",
    unit="labour hours per hectare", source=None, confidence="D",
    why="Purchase price of one hectare of productive farmland for the "
        "household's own staple supply. Not tied to FOREST_COST_PER_HA "
        "or to any attested land price; an independent, invented "
        "figure for a different land use.")

DRAUGHT_HERD = "draught_animal_kg"   # the held stock whose dung the transitional manure rule spreads
DRAUGHT_HERD_SPECIES_ROW = "cattle_kg"   # the draught recipe's dung and fodder factors are the cattle row's (95_herds.json)
