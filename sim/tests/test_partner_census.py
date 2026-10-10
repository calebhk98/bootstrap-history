"""The Han census of AD 2 is the people on the Han economy's tiles: the file adds up to the treatise's own total,
every person is placed on a held tile, no seat lies more than two tile widths from its tile, and the
placement agrees with the civilisation file's population (reads data and the map, no game)."""

QUICK_TOPIC = True

import json
import math
import os

from .harness import check

from sim.engine.data import load_civ
from sim.geography.api import haversine_km, tile_facts, tiles_held
from sim.world import census

TREATISE_TOTAL_PERSONS = 57_671_401   # Hanshu, Dili zhi, the figure the treatise itself gives for 2 AD

file = census.load_census("han_ad2_census")
entries = file["entries"]
persons = sum(entry["persons"] for entry in entries)
check("the commanderies and kingdoms are all there", len(entries) == 103, len(entries))
check("the persons add up to the treatise's total to within a rounding of one", abs(persons - TREATISE_TOTAL_PERSONS) <= 1, persons)

civ = load_civ("han_china_100ad")
held = tiles_held(civ)
located = {tile: (tile_facts(tile)["lat"], tile_facts(tile)["lon"]) for tile in held}
placed, farthest = census.place_on_nearest_tile(entries, located, haversine_km)
check("every person is placed on a tile the country holds", set(placed) <= set(held) and abs(sum(placed.values()) - persons) < 1e-6, None)

grid = json.load(open(os.path.join(os.path.dirname(census.CENSUS_FOLDER), "geography", "tile_grid.json")))
tile_width_km = 2.0 * math.sqrt(2.0 * grid["target_tile_area_km2"] / (3.0 * math.sqrt(3.0)))
check("no seat lies more than two tile widths from the tile its people are given", farthest <= 2.0 * tile_width_km, (farthest, tile_width_km))
check("the census agrees with the civilisation file's population to within a tenth",
      abs(persons / civ["population"] - 1.0) < 0.1, (persons, civ["population"]))
check("the civilisation names the census", civ.get("population_census") == "han_ad2_census", None)

nowhere, none_far = census.place_on_nearest_tile(entries, {}, haversine_km)
check("with no held tiles nothing is placed", nowhere == {} and none_far == 0.0, None)
one, _ = census.place_on_nearest_tile(entries[:2], {"a": (0.0, 0.0), "b": (0.0, 1.0)}, lambda la, lo, lb, lc: abs(lo - lc))
check("an entry goes to the nearest tile", set(one) <= {"a", "b"} and sum(one.values()) == sum(e["persons"] for e in entries[:2]), one)
