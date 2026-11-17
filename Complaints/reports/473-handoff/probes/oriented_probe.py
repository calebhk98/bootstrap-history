"""Why a processor placed beside its fixed input gets no tile: per candidate tile, the hands spare, the room in the input's
market area and the haul cost, at each call. Usage: python3 oriented_probe.py <civ> <recipe>"""
import math, random, sys
from sim.economy import location_inputs
from sim.engine.ui_port import Sim, load, load_civ
civ, wanted_recipe = sys.argv[1], sys.argv[2]
original = location_inputs.place_oriented
calls = []
def probe(setup, record, area_map, carriage, recipe, fixed, shares, tiles):
    result = original(setup, record, area_map, carriage, recipe, fixed, shares, tiles)
    if recipe.recipe_id == wanted_recipe:
        room = {good: location_inputs.area_room(record, setup, area_map, good, maker) for good, maker in fixed.items()}
        used = location_inputs.committed_hours(record, setup)
        hours_per_run = math.fsum(recipe.labour_hours.values())
        rows = []
        for tile in tiles:
            people = setup.opening_population_by_tile.get(tile, 0.0)
            free = people * setup.working_share * setup.working_hours_per_year
            rows.append((tile, people, free, used.get(tile, 0.0), {good: room[good].get(area_map.area_of(good, tile), 0.0) for good in fixed}))
        calls.append((math.fsum(runs for _a, runs in shares), hours_per_run, rows, result))
    return result
location_inputs.place_oriented = probe
from sim.economy import opening
opening.location_inputs.place_oriented = probe
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
from sim.economy import api as economy_api
economy = economy_api.blank_economy(setup)
print("working_share", setup.working_share, "hours per year", setup.working_hours_per_year, "calls", len(calls))
wanted, hours_per_run, rows, result = calls[-1]
print("last call: runs wanted %.4g hours per run %.4g -> %s" % (wanted, hours_per_run, result))
for tile, people, free, used, room in rows:
    print("   %-20s people %8.0f free hours %10.4g committed %10.4g spare %10.4g room %s" % (tile, people, free, used, free - used, {g: round(v, 1) for g, v in room.items()}))
