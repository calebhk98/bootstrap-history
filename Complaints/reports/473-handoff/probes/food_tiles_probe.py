"""Which food each tile makes at the opening and which market areas its goods trade in.
Usage: python3 food_tiles_probe.py <civ>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
hunger = setup.hunger_need
need = next(spec for spec in setup.basket_for(setup.capital_tile).needs if spec.need_id == hunger)
food = dict(need.goods)
print("food goods:", sorted(food))
made = defaultdict(lambda: defaultdict(float))
for key, producer in economy.record.producers.items():
    recipe = setup.recipes[producer.recipe_id]
    for good, quantity in recipe.outputs.items():
        if good in food:
            made[producer.tile][good] += producer.expected_sales * producer.yield_factor * quantity * food[good]
people = defaultdict(float)
for key, cohort in economy.record.cohorts.items():
    people[cohort.tile] += cohort.people
for tile in sorted(people):
    floor = need.subsistence_per_person * people[tile]
    total = sum(made[tile].values())
    top = sorted(made[tile].items(), key=lambda item: -item[1])[:4]
    print("%-14s people %8.0f fert %.3f food made/floor %5.2f  %s" % (tile, people[tile], setup.tiles[tile].fertility, total / floor, " ".join("%s %.2f" % (good, value / floor) for good, value in top)))
print([name for name in dir(setup) if "area" in name or "market" in name or "route" in name or "neigh" in name or "carri" in name])
print([name for name in dir(economy.record) if not name.startswith("__")])
