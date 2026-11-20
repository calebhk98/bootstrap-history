import random, sys
from sim.economy import api as economy_api
from sim.economy import opening_runs, sites
from sim.engine.ui_port import Sim, load, load_civ
civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
record = economy.record
recipes = setup.recipes
for recipe_id in ("silver_jarosite_kg", "lead_kg", "jarosite_ore_kg"):
    recipe = recipes[recipe_id]
    print(recipe_id, "inputs", dict(recipe.inputs), "| hard", dict(recipe.hard_inputs), "| plant", dict(recipe.plant_goods), recipe.plant_life_years)
final = {"nation": dict(record.goods.opening_demand)}
prices = {each: price for each, price in setup.opening_prices.items() if each in setup.specs and price > 0.0}
print("jarosite ore in prices:", "jarosite_ore_kg" in prices, "| in specs:", "jarosite_ore_kg" in setup.specs, "| opening price", setup.opening_prices.get("jarosite_ore_kg"))
ceilings = opening_runs.run_ceilings(recipes, sites.limits_by_recipe(setup.site_limits))
ranked, runs = opening_runs.choose_recipes(final, recipes, prices, setup.opening_wages, setup.opening_rate, ceilings)
required = opening_runs.required_quantities(final, runs, recipes)
for good in ("silver_kg", "lead_kg", "jarosite_ore_kg", "galena_kg", "silver_ore_kg", "charcoal_kg"):
    print("%-16s final %.5g required %.5g ranked %s" % (good, final["nation"].get(good, 0.0), required.get(good, 0.0), ranked.get(good)))
print("runs jarosite_ore_kg", runs.get("jarosite_ore_kg"))
main = opening_runs.main_outputs(recipes, prices)
print("main of lead_kg recipe:", main.get("lead_kg"), "| by-product goods with users:", sorted(opening_runs.by_product_users(recipes, main))[:30])
import inspect
from sim.economy import opening
print([name for name in dir(opening) if "runs" in name or "place" in name][:30])
