"""The opening's producers by recipe: runs sized, hours and value at the opening's prices, tiles. Writes JSON.
Usage: python3 opening_sizes.py <civ> <out.json>"""
import json, random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.engine.ui_port import Sim, load, load_civ
civ, out = sys.argv[1], sys.argv[2]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
rows = defaultdict(lambda: [0.0, 0.0, 0.0, 0])
for key, producer in economy.record.producers.items():
    recipe = setup.recipes[producer.recipe_id]
    row = rows[producer.recipe_id]
    row[0] += producer.expected_sales
    row[1] += producer.expected_sales * sum(recipe.labour_hours.values())
    row[2] += producer.expected_sales * producer.yield_factor * sum(setup.opening_prices.get(good, 0.0) * quantity for good, quantity in recipe.outputs.items())
    row[3] += 1
money = setup.currency_id
book = economy.record.book
json.dump({"recipes": rows, "prices": dict(setup.opening_prices), "wages": dict(setup.opening_wages),
           "household_cash": sum(book.balance(key, money) for key in economy.record.cohorts),
           "producer_cash": sum(book.balance(producer.agent_id, money) for producer in economy.record.producers.values())}, open(out, "w"), default=float)
print("hours %.4g value %.4g producers %d" % (sum(r[1] for r in rows.values()), sum(r[2] for r in rows.values()), sum(r[3] for r in rows.values())))
