"""What held the first year's runs under what the opening sized, for the recipes that fall furthest short: for each of
their inputs the units the sized runs take against what their makers held before the year plus what they got in it (worked
out from the stock after and the runs worked), and whether the whole economy made that input (runs worked over runs sized of
its makers); the runs their land grant allows; the runs staffed.
Usage: python3 first_year_limits_probe.py <civ> [<recipes shown>]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ = sys.argv[1]
shown = int(sys.argv[2]) if len(sys.argv) > 2 else 10
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
record = economy.record
prices = setup.opening_prices
book = record.book


def value_of_run(recipe_id):
    return sum(prices.get(good, 0.0) * quantity for good, quantity in setup.recipes[recipe_id].outputs.items())


before = {}
for key, producer in record.producers.items():
    recipe = setup.recipes[producer.recipe_id]
    before[key] = (producer.recipe_id, producer.expected_sales, producer.capacity_runs,
                   {good: book.stock(producer.agent_id, good, producer.tile) for good in recipe.inputs})
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
economy.step(inputs)
rows = defaultdict(lambda: {"sized": 0.0, "staffed": 0.0, "worked": 0.0, "land": 0.0, "capped": 0, "count": 0,
                            "needed": defaultdict(float), "held": defaultdict(float), "got": defaultdict(float)})
for key, (recipe_id, sized, capacity, held) in before.items():
    producer = record.producers.get(key)
    if producer is None:
        continue
    recipe = setup.recipes[recipe_id]
    row = rows[recipe_id]
    worked = max(0.0, producer.last_runs or 0.0)
    row["sized"] += sized
    row["staffed"] += producer.staffed_runs or 0.0
    row["worked"] += worked
    row["count"] += 1
    cap = producer.land_run_cap
    if cap is not None and cap == cap:
        row["capped"] += 1
        row["land"] += min(cap, sized)
    else:
        row["land"] += sized
    for good, per_run in recipe.inputs.items():
        after = book.stock(producer.agent_id, good, producer.tile)
        row["needed"][good] += per_run * sized
        row["held"][good] += held[good]
        row["got"][good] += max(0.0, after - held[good] + per_run * worked)
made = defaultdict(lambda: [0.0, 0.0])      # good -> [units its makers were sized to make, units they made]
for recipe_id, row in rows.items():
    for good, quantity in setup.recipes[recipe_id].outputs.items():
        made[good][0] += quantity * row["sized"]
        made[good][1] += quantity * row["worked"]
ranked = sorted(rows, key=lambda recipe_id: -(rows[recipe_id]["sized"] - rows[recipe_id]["worked"]) * value_of_run(recipe_id))[:shown]
for recipe_id in ranked:
    row = rows[recipe_id]
    sized = row["sized"] or 1.0
    print("%-28s worked %.2f of the runs sized, staffed %.2f, land allows %.2f (%d of %d makers capped)" % (
        recipe_id[:28], row["worked"] / sized, row["staffed"] / sized, row["land"] / sized, row["capped"], row["count"]))
    for good in sorted(row["needed"], key=lambda each: (row["held"][each] + row["got"][each]) / row["needed"][each] if row["needed"][each] else 9.0):
        needed = row["needed"][good]
        if needed <= 0.0:
            continue
        sized_units, made_units = made[good]
        print("      %-26s had %.2f of what the sized runs take (held %.2f, got %.2f); its makers made %s of what they were sized for" % (
            good[:26], (row["held"][good] + row["got"][good]) / needed, row["held"][good] / needed, row["got"][good] / needed,
            "%.2f" % (made_units / sized_units) if sized_units > 0.0 else "nothing: no maker"))
