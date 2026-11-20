"""For the recipes the opening places beside a fixed-site input: the tiles their makers stand on, the tiles where each fixed input is
made, and how much of the output's use (by the producers that take it as an input) sits in a market area of the output that
holds one of its makers.
Usage: python3 oriented_cover_probe.py <civ>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, location_inputs, sites
from sim.economy.producers import paying_output
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
record, area_map = economy.record, economy.area_map
by_limits = sites.limits_by_recipe(setup.site_limits)
makers = defaultdict(lambda: defaultdict(float))          # recipe -> tile -> runs sized
maker_of_good = {}
for producer in record.producers.values():
    makers[producer.recipe_id][producer.tile] += producer.expected_sales
    for good in setup.recipes[producer.recipe_id].outputs:
        maker_of_good.setdefault(good, producer.recipe_id)
use = defaultdict(lambda: defaultdict(float))             # good -> tile -> units used a year by producers
for recipe_id, tiles in makers.items():
    recipe = setup.recipes[recipe_id]
    for tile, runs in tiles.items():
        for good, quantity in recipe.inputs.items():
            use[good][tile] += quantity * runs
value = lambda recipe_id: sum(setup.opening_prices.get(good, 0.0) * quantity for good, quantity in setup.recipes[recipe_id].outputs.items())
rows = []
for recipe_id, tiles in makers.items():
    recipe = setup.recipes[recipe_id]
    if sites.is_sited(recipe, by_limits):
        continue
    fixed = location_inputs.fixed_inputs(recipe, maker_of_good, setup.recipes, by_limits)
    if not fixed:
        continue
    main = paying_output(recipe, setup.opening_prices)
    areas_with_maker = {area_map.area_of(main, tile) for tile in tiles}
    used = use[main]
    total = sum(used.values())
    local = sum(units for tile, units in used.items() if area_map.area_of(main, tile) in areas_with_maker)
    rows.append((sum(tiles.values()) * value(recipe_id), recipe_id, main, len(tiles), fixed, total, local))
print("recipes placed beside a fixed-site input, largest first by the value of their sized output:")
for worth, recipe_id, main, count, fixed, total, local in sorted(rows, reverse=True)[:20]:
    inputs = ", ".join("%s (made on %d tiles)" % (good, len(makers[maker])) for good, maker in fixed.items())
    print("   %-26s %9.3g  makers on %2d tiles; fixed inputs: %s; producers' use of %s in an area with a maker: %s" % (
        recipe_id[:26], worth, count, inputs, main, "%.2f" % (local / total) if total else "no producer uses it"))
