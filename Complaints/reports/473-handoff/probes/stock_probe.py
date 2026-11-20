"""Where producers' stock piles up over a member's spin-up: per recipe, every few years, expected sales, capacity and worked runs
(shares of the opening's expected sales), the value of its output stock over the value of a year's expected sales, and its
paying output's price over full unit cost; the recipes ranked by the value of stock held at the end.
Usage: python3 stock_probe.py <civ> <member> <years> <every>"""
import math, random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy import unit_cost
from sim.economy.producers import expected_output_prices, live_input_prices, live_wages, paying_output
from sim.economy.rates import own_rate
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages
from sim.markets.spin_up_ensemble import cash_factor

civ, member, years, every = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
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
        prices = {good: view.price(good, economy.area_map.area_of(good, producer.tile)) for good in recipe.outputs}
        row["expected"] += producer.expected_sales
        row["capacity"] += producer.capacity_runs
        row["worked"] += max(producer.last_runs, 0.0)
        for good, made in recipe.outputs.items():
            price = prices.get(good)
            if price is None:
                continue
            held = view.stock(producer.agent_id, good, producer.tile) - recipe.inputs.get(good, 0.0) * producer.capacity_runs
            row["stock_value"] += max(0.0, held) * price
            row["sales_value"] += producer.expected_sales * made * producer.yield_factor * price
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
for year in range(years):
    economy.step(inputs)
    if (year + 1) % every == 0 or year + 1 == years:
        history.append((year + 1, snapshot()))
last = history[-1][1]
total_stock = sum(row["stock_value"] for row in last.values()) or 1.0
total_sales = sum(row["sales_value"] for row in last.values()) or 1.0
print("stock held by producers at the end is %.2f of a year's expected sales, by value" % (total_stock / total_sales))
ranked = sorted(last, key=lambda recipe_id: -last[recipe_id]["stock_value"])[:14]
for recipe_id in ranked:
    base = opening[recipe_id] or 1.0
    print("%-30s %4.1f%% of all stock, %4.1f%% of sales" % (recipe_id[:30], 100 * last[recipe_id]["stock_value"] / total_stock,
                                                         100 * last[recipe_id]["sales_value"] / total_sales))
    for year, rows in history:
        row = rows[recipe_id]
        print("     year %2d  expected %5.2f  capacity %5.2f  worked %5.2f  stock/sales %5.2f  price/cost %5.2f" % (
            year, row["expected"] / base, row["capacity"] / base, row["worked"] / base,
            row["stock_value"] / row["sales_value"] if row["sales_value"] else float("nan"),
            row["ratio_sum"] / row["ratio_weight"] if row["ratio_weight"] else float("nan")))
