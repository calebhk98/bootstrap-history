"""What the opening places for the coin metal: the money's yearly loss in units of the backing good, and the capacity and
expected sales of every producer on the chain. Usage: python3 coin_opening_probe.py <civ>"""
import random, sys
from sim.economy import api as economy_api
from sim.economy import opening_metal, opening_runs, sites, mint
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
record = economy.record
spec = record.currency
print("regime", spec.regime, "backing", spec.backing_good, "per unit", spec.backing_per_unit, "loss share", mint.loss_share(setup, spec))
print("money supply", record.book.money_supply(spec.currency_id), "yearly replacement (units of the good)", opening_metal.yearly_replacement(setup, record))
print("opening demand for the backing good", record.goods.opening_demand.get(spec.backing_good))
chain = ("silver", "jarosite", "galena", "lead_", "gold", "copper", "bronze")
totals = {}
for key, producer in sorted(record.producers.items()):
    if any(word in producer.recipe_id for word in chain):
        row = totals.setdefault(producer.recipe_id, [0, 0.0, 0.0])
        row[0] += 1
        row[1] += producer.capacity_runs
        row[2] += producer.expected_sales
for recipe_id, (count, capacity, sales) in sorted(totals.items()):
    recipe = setup.recipes[recipe_id]
    print("%-26s producers %2d capacity runs %.5g expected sales (runs) %.5g outputs %s" % (recipe_id, count, capacity, sales, dict(recipe.outputs)))
final = {"nation": dict(record.goods.opening_demand)}
prices = {each: price for each, price in setup.opening_prices.items() if each in setup.specs and price > 0.0}
ceilings = opening_runs.run_ceilings(setup.recipes, sites.limits_by_recipe(setup.site_limits))
_ranked, runs = opening_runs.choose_recipes(final, setup.recipes, prices, setup.opening_wages, setup.opening_rate, ceilings)
for recipe_id in sorted(runs):
    if any(word in recipe_id for word in chain) and runs[recipe_id] > 0.0:
        print("chosen runs %-26s %.5g" % (recipe_id, runs[recipe_id]))
