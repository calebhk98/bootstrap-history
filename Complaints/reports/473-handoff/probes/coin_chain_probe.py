"""Why the opening places the coin metal's makers where it does: the recipes that make the backing good and their ores,
whether each is site-bound, its declared limits, its ceiling, its unit cost and the runs the opening chooses.
Usage: python3 coin_chain_probe.py <civ>"""
import random, sys
from sim.economy import opening_runs, sites, opening_metal
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
by_limits = sites.limits_by_recipe(setup.site_limits)
recipes = setup.recipes
good = setup.currency.backing_good if hasattr(setup, "currency") else None
print("backing good", good, "| site limits declared for", len(by_limits), "recipes |", len(recipes), "recipes")
ceilings = opening_runs.run_ceilings(recipes, by_limits)
prices = {each: price for each, price in setup.opening_prices.items() if each in setup.specs and price > 0.0}
costs = opening_runs.unit_costs(recipes, prices, setup.opening_wages, setup.opening_rate)
seen, queue = set(), [good] if good else []
names = [recipe_id for recipe_id, recipe in recipes.items() if any("silver" in output or "jarosite" in output or "galena" in output for output in recipe.outputs)]
for recipe_id in sorted(names):
    recipe = recipes[recipe_id]
    limits = by_limits.get(recipe_id, {})
    print("%-22s site_bound %-5s deposit_bound %-5s limits on %2d tiles (runs %s) ceiling %s" % (
        recipe_id, recipe.site_bound, recipe.deposit_bound, len(limits),
        "%.4g" % sum(limit.capacity_runs_per_year for limit in limits.values()) if limits else "-", ceilings.get(recipe_id, "none")))
    print("      outputs", dict(recipe.outputs), "hard inputs", {k: v for k, v in recipe.hard_inputs.items()})
    allowed = getattr(setup, "recipe_allowed", None)
    if allowed is not None:
        try:
            print("      allowed on tiles:", sum(1 for tile in setup.tiles if allowed(recipe_id, tile)), "of", len(setup.tiles))
        except Exception as error:
            print("      recipe_allowed:", type(allowed), error)
for name in ("silver_kg", "silver_ore_kg", "jarosite_ore_kg", "galena_kg", "lead_kg"):
    print(name, "price", prices.get(name), "costs", [(round(cost, 4), recipe_id) for cost, recipe_id in costs.get(name, [])])
