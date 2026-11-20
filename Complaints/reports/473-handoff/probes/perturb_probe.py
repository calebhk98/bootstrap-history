"""Does the economy hold its course when the content changes? One spin-up of a civilisation's opening with a change made
to its setup first: a good's opening price multiplied, or every recipe that makes a good taken out. Prints the totals over
the last years of the trimmed stage (as shares of the unchanged run's first year when a baseline file is given) and the
mean yearly move of each, so runs can be laid side by side.
Usage: [ABLATE=name] python3 perturb_probe.py <civ> none|price:<good>:<factor>|drop:<good> <out.jsonl>"""
import dataclasses, json, random, sys
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages

civ, change, out = sys.argv[1], sys.argv[2], sys.argv[3]
_tree, _prices, nodes, _wages, _goods = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
kind, _colon, rest = change.partition(":")
if kind == "price":
    good, _colon, factor = rest.partition(":")
    prices = dict(setup.opening_prices)
    prices[good] = prices[good] * float(factor)
    setup = dataclasses.replace(setup, opening_prices=prices)
elif kind == "drop":
    recipes = {recipe_id: recipe for recipe_id, recipe in setup.recipes.items() if rest not in recipe.outputs}
    print("recipes taken out:", sorted(set(setup.recipes) - set(recipes)))
    setup = dataclasses.replace(setup, recipes=recipes)
import os
if os.environ.get("ABLATE"):       # experiment switches (ablations.py beside this file)
    import ablations
    ablations.apply(os.environ["ABLATE"])
watched, rows = spin_up_stages.replay_opening(setup, 1.0)
names = ("hired_hours", "real_output", "price_level", "wage", "unmet_need", "food_need", "rate", "inventory_value", "money_supply")
with open(out, "w") as handle:
    for row in rows:
        kept = {name: row.get(name) for name in ("stage", "year") + names}
        kept["prices"] = row.get("prices")
        kept["price_weights"] = row.get("price_weights")
        kept["member"] = 0
        handle.write(json.dumps(kept, default=float) + "\n")
print("done", change)
