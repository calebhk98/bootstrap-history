"""Whether the opening's input-output passes settle for the coin metal: the runs `opening_runs.required_runs` returns for the
makers of the backing good and of their ores when the pass bound is one more, two more and so on. A settled answer does not
change with the bound. Usage: python3 coin_passes_probe.py <civ>"""
import random, sys
from sim.economy import api as economy_api
from sim.economy import opening_runs, sites
from sim.engine.ui_port import Sim, load, load_civ
civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
record = economy_api.blank_economy(setup).record
recipes = setup.recipes
good = record.currency.backing_good
final = {"nation": dict(record.goods.opening_demand)}
prices = {each: price for each, price in setup.opening_prices.items() if each in setup.specs and price > 0.0}
ceilings = opening_runs.run_ceilings(recipes, sites.limits_by_recipe(setup.site_limits))
ranked, _runs = opening_runs.choose_recipes(final, recipes, prices, setup.opening_wages, setup.opening_rate, ceilings)
main = opening_runs.main_outputs(recipes, prices)
makers = [recipe_id for recipe_id in sorted(recipes) if recipes[recipe_id].outputs.get(good, 0.0) > 0.0]
inputs = sorted({used for maker in makers for used in recipes[maker].hard_inputs})
watched = makers + [recipe_id for recipe_id in sorted(recipes) if any(recipes[recipe_id].outputs.get(used, 0.0) > 0.0 for used in inputs)
                    and recipe_id not in makers]
print("ranked for", good, ranked.get(good))
bound = opening_runs.INPUT_OUTPUT_PASSES
for extra in range(4):
    opening_runs.INPUT_OUTPUT_PASSES = bound + extra
    runs = opening_runs.required_runs(final, ranked, recipes, ceilings, None, main)
    print("passes %d: %s" % (bound + extra, "  ".join("%s %.5g" % (recipe_id, runs.get(recipe_id, 0.0)) for recipe_id in watched if "charcoal" not in recipe_id and "wood" not in recipe_id)))
