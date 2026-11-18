"""The makers of chosen recipes, summed, by year: coin, the coin target, the cost of a year at capacity and at expected sales,
capacity, expected sales, runs staffed and worked (as shares of the opening's expected sales), and what they hold of inputs.
Usage: python3 recipe_coin_probe.py <civ> <member> <years> <recipe> [<recipe> ...]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy.producers_close import working_capital_target
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages
from sim.markets.spin_up_ensemble import cash_factor

civ, member, years, recipes = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
if cash_factor(member) != 1.0:
    spin_up_stages.perturb_household_cash(economy, cash_factor(member))
inputs = spin_up_stages.year_inputs(economy)
record = economy.record
money = setup.currency_id
book = record.book
opening = defaultdict(float)
for producer in record.producers.values():
    opening[producer.recipe_id] += producer.expected_sales

def show(label, prices, wages):
    for recipe_id in recipes:
        recipe = setup.recipes[recipe_id]
        row = defaultdict(float)
        for producer in record.producers.values():
            if producer.recipe_id != recipe_id:
                continue
            row["coin"] += book.balance(producer.agent_id, money)
            row["target"] += producer.cash_target
            row["capacity"] += producer.capacity_runs
            row["expected"] += producer.expected_sales
            row["worked"] += max(producer.last_runs, 0.0)
            row["staffed"] += producer.staffed_runs or 0.0
            row["count"] += 1
            for good, per_run in recipe.inputs.items():
                row["held:" + good] += book.stock(producer.agent_id, good, producer.tile) / per_run
            for good, per_run in recipe.outputs.items():
                if per_run > 0.0:
                    row["out:" + good] += book.stock(producer.agent_id, good, producer.tile) / per_run
        base = opening[recipe_id] or 1.0
        year_cost = working_capital_target(recipe, 1.0, prices, wages)
        print("%-10s %-26s coin %9.4g target %9.4g cost/run %8.4g coin buys %5.2f | cap %.2f exp %.2f staffed %.2f worked %.2f | %s" % (
            label, recipe_id[:26], row["coin"], row["target"], year_cost, row["coin"] / year_cost / base if year_cost else float("nan"),
            row["capacity"] / base, row["expected"] / base, row["staffed"] / base, row["worked"] / base,
            " ".join("%s %.2f" % (name, value / base) for name, value in sorted(row.items()) if ":" in name)))

show("opening", setup.opening_prices, setup.opening_wages)
for year in range(years):
    outcome = economy.step(inputs)
    prices = dict(setup.opening_prices); prices.update({good: price for good, price in outcome.prices.items() if price})
    wages = dict(setup.opening_wages); wages.update({trade: wage for trade, wage in outcome.wages.items() if wage})
    show("year %d" % year, prices, wages)
