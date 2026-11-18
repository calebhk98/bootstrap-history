"""The opening's makers of a good and, level by level, of their inputs and plant goods: recipe, runs, tiles.
Usage: python3 chain_probe.py <civ> <good> [depth]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.engine.ui_port import Sim, load, load_civ
civ, good = sys.argv[1], sys.argv[2]
depth = int(sys.argv[3]) if len(sys.argv) > 3 else 3
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
makers = defaultdict(list)
for producer in economy.record.producers.values():
    for output in setup.recipes[producer.recipe_id].outputs:
        makers[output].append(producer)
seen = set()
def show(good, level):
    if good in seen or level > depth:
        return
    seen.add(good)
    by_recipe = defaultdict(lambda: [0.0, set()])
    for producer in makers.get(good, []):
        by_recipe[producer.recipe_id][0] += producer.expected_sales
        by_recipe[producer.recipe_id][1].add(producer.tile)
    if not by_recipe:
        print("  " * level + "%s: no opening maker" % good)
    for recipe_id, (runs, tiles) in sorted(by_recipe.items()):
        recipe = setup.recipes[recipe_id]
        print("  " * level + "%s <- %s runs %.4g on %s | inputs %s | plant %s (life %s) | hours %s" % (good, recipe_id, runs, sorted(tiles)[:4],
              {name: round(quantity, 3) for name, quantity in recipe.inputs.items()}, {name: round(quantity, 3) for name, quantity in recipe.plant_goods.items()},
              recipe.plant_life_years, {name: round(hours, 1) for name, hours in recipe.labour_hours.items()}))
        for name in list(recipe.inputs) + list(recipe.plant_goods):
            show(name, level + 1)
show(good, 0)
