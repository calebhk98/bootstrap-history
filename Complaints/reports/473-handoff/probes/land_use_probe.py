"""The land the opening's producers take, by recipe: hectares at their expected sales, the land a run takes, runs, what a run makes,
and the land cap the land market set against the runs sized. Usage: python3 land_use_probe.py <civ>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, titles_ground
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
record = economy.record
rows = defaultdict(lambda: [0.0, 0.0, 0.0, 0])
for producer in record.producers.values():
    per_run = setup.land_per_run.get(producer.recipe_id, 0.0)
    if per_run <= 0.0:
        continue
    row = rows[producer.recipe_id]
    row[0] += producer.expected_sales * per_run
    row[1] += producer.expected_sales
    row[2] += producer.capacity_runs * per_run
    row[3] += 1 if producer.land_run_cap is not None else 0
arable = sum(titles_ground.arable_hectares(record, tile_id, tile) for tile_id, tile in setup.tiles.items())
total = sum(row[0] for row in rows.values())
print("arable %.4g ha; producers' runs take %.4g ha (%.0f%%)" % (arable, total, 100 * total / arable))
print("%-30s %11s %7s %10s %11s %6s  %s" % ("recipe", "hectares", "share", "ha a run", "runs", "capped", "a run makes"))
for recipe_id, row in sorted(rows.items(), key=lambda item: -item[1][0])[:16]:
    recipe = setup.recipes[recipe_id]
    print("%-30s %11.4g %6.1f%% %10.4g %11.4g %6d  %s" % (recipe_id[:30], row[0], 100 * row[0] / total, setup.land_per_run[recipe_id], row[1], row[3],
          {good: round(quantity, 1) for good, quantity in recipe.outputs.items()}))
