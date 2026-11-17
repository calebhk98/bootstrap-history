"""The opening's producers of site-bound recipes with no declared site limit: tiles they stand on and hours they want.
Usage: python3 unsited_list.py <civ>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, sites
from sim.engine.ui_port import Sim, load, load_civ
civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
by_limits = sites.limits_by_recipe(setup.site_limits)
rows = defaultdict(lambda: [0.0, set()])
hours_by_tile = defaultdict(float)
unsited_by_tile = defaultdict(float)
for key, producer in economy.record.producers.items():
    recipe = setup.recipes[producer.recipe_id]
    hours = producer.expected_sales * sum(recipe.labour_hours.values())
    hours_by_tile[producer.tile] += hours
    if sites.runs_anywhere(recipe, by_limits):
        rows[producer.recipe_id][0] += hours
        rows[producer.recipe_id][1].add(producer.tile)
        unsited_by_tile[producer.tile] += hours
total = sum(hours_by_tile.values())
print("hours sized %.4g; by site-bound recipes with no declared limit %.4g" % (total, sum(row[0] for row in rows.values())))
for recipe_id, (hours, tiles) in sorted(rows.items(), key=lambda pair: -pair[1][0])[:25]:
    print("   %-34s %10.4g hours  tiles %s" % (recipe_id, hours, sorted(tiles) if len(tiles) < 4 else len(tiles)))
print("by tile: hours sized, of which unsited site-bound")
for tile in sorted(hours_by_tile):
    print("   %-22s %10.4g %10.4g  people %9.0f" % (tile, hours_by_tile[tile], unsited_by_tile[tile], setup.opening_population_by_tile.get(tile, 0.0)))
