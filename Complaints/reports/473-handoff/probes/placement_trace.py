"""How the opening places chosen recipes: which branch (oriented to fixed inputs, or split over an area) and the runs each tile gets.
Usage: python3 placement_trace.py <civ> <recipe> [<recipe> ...]"""
import random, sys
from sim.economy import opening, location, location_inputs
from sim.engine.ui_port import Sim, load, load_civ

civ, wanted = sys.argv[1], set(sys.argv[2:])
original_split, original_oriented, original_add, original_fixed = location.opening_split, location_inputs.place_oriented, opening._add_producers, location_inputs.fixed_inputs

def split(setup, recipe, area, runs):
    result = original_split(setup, recipe, area, runs)
    if recipe.recipe_id in wanted:
        print("  split", recipe.recipe_id, "area", area.area_id, "anchor", area.anchor_tile, "tiles", len(area.tiles), "runs %.4g" % runs, "->", {tile: round(value, 1) for tile, value in result.items()})
    return result

def oriented(setup, record, area_map, carriage, recipe, fixed, shares, tiles):
    result = original_oriented(setup, record, area_map, carriage, recipe, fixed, shares, tiles)
    if recipe.recipe_id in wanted:
        print("  oriented", recipe.recipe_id, "fixed inputs", fixed, "shares", [(area.area_id, round(runs, 1)) for area, runs in shares], "tiles", len(tiles), "->", {tile: round(value, 1) for tile, value in result.items()})
    return result

def fixed_inputs(recipe, incumbents, recipes, by_limits):
    result = original_fixed(recipe, incumbents, recipes, by_limits)
    if recipe.recipe_id in wanted:
        print("  fixed_inputs", recipe.recipe_id, "->", result, "inputs", dict(recipe.inputs), "site_bound", recipe.site_bound)
    return result

location.opening_split = split
location_inputs.place_oriented = oriented
location_inputs.fixed_inputs = fixed_inputs
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
from sim.economy import api as economy_api
economy = economy_api.blank_economy(setup)
for key, producer in economy.record.producers.items():
    if producer.recipe_id in wanted:
        print("  producer", key, "expected %.4g capacity %.4g" % (producer.expected_sales, producer.capacity_runs))
