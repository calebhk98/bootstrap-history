"""Which recipes lose the hired hours over a member's spin-up: per recipe, at the years asked, the hours its staffed runs take
(a share of all hours staffed in the first year printed), with its expected sales, capacity and worked runs against the
opening's expected sales and its paying output's price over full unit cost; the recipes ranked by the hours they lose
between the first and the last year printed, then those that gain most.
Usage: python3 hours_fall_probe.py <civ> <member> <year,year,...>"""
import math, random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy import unit_cost
from sim.economy.producers import expected_output_prices, live_input_prices, live_wages, paying_output
from sim.economy.rates import own_rate
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages
from sim.markets.spin_up_ensemble import cash_factor

civ, member, marks = sys.argv[1], int(sys.argv[2]), [int(each) for each in sys.argv[3].split(",")]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
if cash_factor(member) != 1.0:
    spin_up_stages.perturb_household_cash(economy, cash_factor(member))
inputs = spin_up_stages.year_inputs(economy)
record = economy.record
opening = defaultdict(float)
for producer in record.producers.values():
    opening[producer.recipe_id] += producer.expected_sales


def snapshot():
    view = economy.view()
    rate = own_rate(view, setup.currency_id)
    rows = defaultdict(lambda: defaultdict(float))
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        row = rows[producer.recipe_id]
        hours = sum(recipe.labour_hours.values())
        row["hours"] += (producer.staffed_runs or 0.0) * hours
        row["expected"] += producer.expected_sales
        row["capacity"] += producer.capacity_runs
        row["worked"] += max(producer.last_runs, 0.0)
        prices = {good: view.price(good, economy.area_map.area_of(good, producer.tile)) for good in recipe.outputs}
        good = paying_output(recipe, prices)
        if prices.get(good) is not None:
            cost = unit_cost.full_cost_per_unit(recipe, good, expected_output_prices(producer, recipe, view), live_input_prices(producer, recipe, view),
                                                live_wages(producer, recipe, view), rate, producer.land_rent_per_run, producer.yield_factor)
            if cost is not None and math.isfinite(cost) and cost > 0.0:
                weight = max(producer.last_runs, 0.0) + 1e-9
                row["ratio_sum"] += weight * prices[good] / cost
                row["ratio_weight"] += weight
    return rows


history = []
for year in range(max(marks)):
    economy.step(inputs)
    if year + 1 in marks:
        history.append((year + 1, snapshot()))
first, last = history[0][1], history[-1][1]
total = sum(row["hours"] for row in first.values()) or 1.0
print("hours staffed, as a share of the year %d total: " % history[0][0] + "  ".join(
    "year %d %.3f" % (year, sum(row["hours"] for row in rows.values()) / total) for year, rows in history))
recipes = set(first) | set(last)
change = {recipe_id: (last[recipe_id]["hours"] - first[recipe_id]["hours"]) / total for recipe_id in recipes}


def show(recipe_id):
    base = opening[recipe_id] or 1.0
    print("%-32s %+6.3f of all hours" % (recipe_id[:32], change[recipe_id]))
    for year, rows in history:
        row = rows[recipe_id]
        print("     year %2d  hours %.3f  expected %5.2f  capacity %5.2f  worked %5.2f  price/cost %5.2f" % (
            year, row["hours"] / total, row["expected"] / base, row["capacity"] / base, row["worked"] / base,
            row["ratio_sum"] / row["ratio_weight"] if row["ratio_weight"] else float("nan")))


print("-- lose most")
for recipe_id in sorted(recipes, key=lambda each: change[each])[:10]:
    show(recipe_id)
print("-- gain most")
for recipe_id in sorted(recipes, key=lambda each: -change[each])[:4]:
    show(recipe_id)
