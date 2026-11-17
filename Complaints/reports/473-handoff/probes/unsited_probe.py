"""For a civilisation's opening: the deposit-bound recipes with no declared site (they run anywhere today), whether their output
is a catalogue ore, and what the opening placed of them; and the money's yearly loss against what the opening placed for the
backing good. Usage: python3 unsited_probe.py <civ>"""
import random, sys
from sim.economy import api as economy_api
from sim.economy import opening_metal, sites, mint
from sim.engine.ui_port import Sim, load, load_civ
civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
record = economy.record
by_limits = sites.limits_by_recipe(setup.site_limits)
ore_of = {}
placed = {}
for producer in record.producers.values():
    placed[producer.recipe_id] = placed.get(producer.recipe_id, 0.0) + producer.capacity_runs
print(civ, "tiles", len(setup.tiles), "| recipes with site limits:", sorted(by_limits))
for recipe_id, recipe in sorted(setup.recipes.items()):
    if recipe.deposit_bound and not by_limits.get(recipe_id):
        print("   no site: %-24s catalogue ore of %-12s placed capacity runs %.5g" % (recipe_id, ore_of.get(recipe_id, "-"), placed.get(recipe_id, 0.0)))
spec = record.currency
good = spec.backing_good
print("money", spec.regime, good, "loss share", mint.loss_share(setup, spec), "yearly replacement", "%.5g" % opening_metal.yearly_replacement(setup, record),
      "opening demand", "%.5g" % record.goods.opening_demand.get(good, 0.0) if good else None)
if good:
    for recipe_id, recipe in sorted(setup.recipes.items()):
        if recipe.outputs.get(good, 0.0) > 0.0:
            print("   makes %s: %-26s placed runs %.5g -> %.5g a year" % (good, recipe_id, placed.get(recipe_id, 0.0), placed.get(recipe_id, 0.0) * recipe.outputs[good]))
