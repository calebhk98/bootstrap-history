"""The opening's placement order against its own rule (a recipe is placed after every recipe that uses what it makes): the recipes
placed before one of their users, with the users that came later and the share of the good's sized use those users are.
Usage: python3 placement_order_probe.py <civ>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, opening
from sim.economy.producers import paying_output
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
record = economy.record
runs = defaultdict(float)
for producer in record.producers.values():
    runs[producer.recipe_id] += producer.expected_sales
order = opening._placement_order(dict(runs), setup.recipes, setup)
place = {recipe_id: index for index, recipe_id in enumerate(order)}
produced = {recipe_id: paying_output(setup.recipes[recipe_id], setup.opening_prices) for recipe_id in runs}
use = defaultdict(lambda: defaultdict(float))       # good -> user recipe -> units a year
for recipe_id, count in runs.items():
    recipe = setup.recipes[recipe_id]
    for good, quantity in recipe.inputs.items():
        use[good][recipe_id] += quantity * count
    if recipe.plant_life_years > 0.0:
        for good, quantity in recipe.plant_goods.items():
            use[good][recipe_id] += quantity * count / recipe.plant_life_years
early = []
for recipe_id in order:
    good = produced[recipe_id]
    late = {user: units for user, units in use[good].items() if place[user] > place[recipe_id] and user != recipe_id}
    if late:
        total = sum(use[good].values())
        early.append((sum(late.values()) / total if total else 0.0, recipe_id, good, late, total))
print("%d recipes placed, %d of them before a user of what they make" % (len(order), len(early)))
for share, recipe_id, good, late, total in sorted(early, reverse=True)[:25]:
    names = ", ".join("%s %.2f" % (user, units / total) for user, units in sorted(late.items(), key=lambda item: -item[1])[:4])
    print("   %-28s placed %3d of %d; users placed later take %.2f of the producers' use of %s: %s" % (
        recipe_id[:28], place[recipe_id] + 1, len(order), share, good, names))
