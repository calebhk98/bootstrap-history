"""Before the opening fits producers to supply: each limited good's supply and what its users want.
Usage: python3 fit_probe.py <civ>"""
import math, random, sys
from sim.economy import opening_runs, sites
from sim.engine.ui_port import Sim, load, load_civ
original = opening_runs.fit_to_supply
seen = {"count": 0}
def probe(setup, record):
    seen["count"] += 1
    by_limits = sites.limits_by_recipe(setup.site_limits)
    fixed = sorted(opening_runs.limited_goods(setup.recipes, by_limits))
    rows = []
    for good in fixed:
        supply = wanted = 0.0
        makers, users = set(), set()
        for key, producer in record.producers.items():
            recipe = setup.recipes[producer.recipe_id]
            made = recipe.outputs.get(good, 0.0)
            if made > 0.0:
                supply += producer.expected_sales * producer.yield_factor * made
                makers.add(producer.recipe_id)
            if sites.is_sited(recipe, by_limits):
                continue
            use = recipe.hard_inputs.get(good, 0.0) + (recipe.plant_goods.get(good, 0.0) / recipe.plant_life_years if recipe.plant_life_years > 0.0 else 0.0)
            if use > 0.0:
                wanted += producer.expected_sales * use
                users.add(producer.recipe_id)
        rows.append((good, supply, wanted, sorted(makers), sorted(users)))
    seen["rows"] = rows
    return original(setup, record)
opening_runs.fit_to_supply = probe
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(sys.argv[1]))
setup = game.view("agent_opening_setup")()
from sim.economy import api as economy_api
economy = economy_api.blank_economy(setup)
print("fits run:", seen["count"], "limited goods:", len(seen["rows"]))
for good, supply, wanted, makers, users in sorted(seen["rows"], key=lambda row: (row[1] / row[2] if row[2] > 0 else 9e9)):
    if wanted > 0.0:
        print("   %-26s supply %10.4g wanted %10.4g share %.3f  makers %s users %s" % (good, supply, wanted, supply / wanted, makers[:3], users[:6]))
