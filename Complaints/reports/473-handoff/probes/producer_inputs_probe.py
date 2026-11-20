"""One producer through the first years: before each year its coin and what it holds of its inputs and plant goods (in runs' worth),
after it the runs staffed and worked and what it holds of its outputs. Usage: python3 producer_inputs_probe.py <civ> <producer key> <years>"""
import random, sys
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ, key, years = sys.argv[1], sys.argv[2], int(sys.argv[3])
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
money = setup.currency_id
book = economy.record.book
recipe = setup.recipes[economy.record.producers[key].recipe_id]
print("recipe inputs", dict(recipe.inputs), "plant", dict(recipe.plant_goods), "life", recipe.plant_life_years, "outputs", dict(recipe.outputs))


def show(label):
    producer = economy.record.producers.get(key)
    if producer is None:
        print(label, "gone")
        return
    held_inputs = {good: round(book.stock(producer.agent_id, good, producer.tile) / per_run, 1) for good, per_run in recipe.inputs.items()}
    held_plant = {good: round(book.stock(producer.agent_id, good, producer.tile) / per_run, 1) for good, per_run in recipe.plant_goods.items()}
    held_outputs = {good: round(book.stock(producer.agent_id, good, producer.tile) / per_run, 1) for good, per_run in recipe.outputs.items() if per_run > 0}
    fields = {name: getattr(producer, name, None) for name in ("capacity_runs", "expected_sales", "last_runs", "staffed_runs", "land_run_cap", "cash_target", "idle_years", "yield_factor")}
    print(label, "coin %.4g" % book.balance(producer.agent_id, money), "| inputs held (runs' worth)", held_inputs, "| plant held", held_plant,
          "| outputs held (runs' worth)", held_outputs, "|", {name: (round(value, 2) if isinstance(value, float) else value) for name, value in fields.items()})


show("opening:")
for year in range(years):
    outcome = economy.step(inputs)
    show("after year %d:" % year)
    print("   prices:", {good: outcome.prices.get(good) for good in list(recipe.inputs) + list(recipe.plant_goods) + list(recipe.outputs)})
