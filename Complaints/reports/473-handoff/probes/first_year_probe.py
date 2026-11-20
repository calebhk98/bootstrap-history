"""The opening against the first year: for each recipe, the runs the opening sized (expected sales), the capacity it placed, the runs
staffed and the runs worked in the first year, valued at the opening's prices; the recipes whose first year falls furthest short.
Usage: python3 first_year_probe.py <civ> [<years>]"""
import random, sys
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ = sys.argv[1]
years = int(sys.argv[2]) if len(sys.argv) > 2 else 1
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
prices = setup.opening_prices
money = setup.currency_id


def value_of_run(recipe_id):
    return sum(prices.get(good, 0.0) * quantity for good, quantity in setup.recipes[recipe_id].outputs.items())


def hours_of_run(recipe_id):
    return sum(setup.recipes[recipe_id].labour_hours.values())


opening = {}
for key, producer in economy.record.producers.items():
    opening[key] = (producer.recipe_id, producer.expected_sales, producer.capacity_runs, economy.record.book.balance(producer.agent_id, money))
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
for year in range(years):
    outcome = economy.step(inputs)
    by_recipe = {}
    for key, (recipe_id, sized, capacity, coin) in opening.items():
        producer = economy.record.producers.get(key)
        row = by_recipe.setdefault(recipe_id, [0.0, 0.0, 0.0, 0.0, 0])
        row[0] += sized
        row[1] += capacity
        row[2] += (producer.staffed_runs or 0.0) if producer is not None else 0.0
        row[3] += max(0.0, producer.last_runs or 0.0) if producer is not None else 0.0
        row[4] += 1
    sized_value = sum(row[0] * value_of_run(recipe_id) for recipe_id, row in by_recipe.items())
    worked_value = sum(row[3] * value_of_run(recipe_id) for recipe_id, row in by_recipe.items())
    sized_hours = sum(row[0] * hours_of_run(recipe_id) for recipe_id, row in by_recipe.items())
    worked_hours = sum(row[3] * hours_of_run(recipe_id) for recipe_id, row in by_recipe.items())
    staffed_hours = sum(row[2] * hours_of_run(recipe_id) for recipe_id, row in by_recipe.items())
    print("year %d: output sized %.4g worked %.4g (%.2f) | hours sized %.4g staffed %.4g worked %.4g (%.2f) | hired %.4g idle %.4g wage %.3f" % (
        year, sized_value, worked_value, worked_value / sized_value, sized_hours, staffed_hours, worked_hours, worked_hours / sized_hours,
        outcome.hired_hours, outcome.idle_hours, outcome.wages.get(setup.unskilled_trade) or 0.0))
    shortfalls = sorted(((row[0] - row[3]) * value_of_run(recipe_id), recipe_id, row) for recipe_id, row in by_recipe.items())
    print("   furthest short (value of output at opening prices; sized, capacity, staffed, worked runs; producers):")
    for short, recipe_id, row in shortfalls[::-1][:14]:
        print("   %10.4g  %-26s sized %10.4g capacity %10.4g staffed %10.4g worked %10.4g (%.2f) hours/run %8.4g  n=%d" % (
            short, recipe_id, row[0], row[1], row[2], row[3], row[3] / row[0] if row[0] else 0.0, hours_of_run(recipe_id), row[4]))
    print("   furthest over:")
    for short, recipe_id, row in shortfalls[:5]:
        print("   %10.4g  %-26s sized %10.4g worked %10.4g" % (short, recipe_id, row[0], row[3]))
