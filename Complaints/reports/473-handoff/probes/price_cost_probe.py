"""How far above or below its makers' cost each good's price sits after some years of a member's spin-up: per producer the
remembered price of its paying output in its own area over its full unit cost (inputs, hands, rent and the capital charge),
as a distribution weighted by the producer's revenue, and the goods that sit furthest from cost.
Usage: python3 price_cost_probe.py <civ> <member> <years>"""
import math, random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy import unit_cost
from sim.economy.producers import expected_output_prices, live_input_prices, live_wages, paying_output
from sim.economy.rates import own_rate
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages
from sim.markets.spin_up_ensemble import cash_factor

civ, member, years = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
if cash_factor(member) != 1.0:
    spin_up_stages.perturb_household_cash(economy, cash_factor(member))
inputs = spin_up_stages.year_inputs(economy)
record = economy.record


def ratios():
    view = economy.view()
    rate = own_rate(view, setup.currency_id)
    found = []
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        if producer.capacity_runs <= 0.0 or producer.yield_factor <= 0.0:
            continue
        prices = {good: view.price(good, economy.area_map.area_of(good, producer.tile)) for good in recipe.outputs}
        good = paying_output(recipe, prices)
        price = prices.get(good)
        if price is None:
            continue
        cost = unit_cost.full_cost_per_unit(recipe, good, expected_output_prices(producer, recipe, view), live_input_prices(producer, recipe, view),
                                            live_wages(producer, recipe, view), rate, producer.land_rent_per_run, producer.yield_factor)
        if cost is None or not math.isfinite(cost) or cost <= 0.0:
            continue
        revenue = max(producer.last_runs, 0.0) * recipe.outputs[good] * producer.yield_factor * price
        found.append((price / cost, revenue, good, producer.recipe_id))
    return found


def report(label):
    found = sorted(ratios())
    total = sum(revenue for _ratio, revenue, _good, _recipe in found) or 1.0
    print(label, "producers", len(found))
    running = 0.0
    marks = [0.1, 0.25, 0.5, 0.75, 0.9]
    quantiles = {}
    for ratio, revenue, _good, _recipe in found:
        running += revenue / total
        for mark in marks:
            if mark not in quantiles and running >= mark:
                quantiles[mark] = ratio
    print("   price over full cost, by revenue: " + "  ".join("p%d %.2f" % (100 * mark, quantiles.get(mark, float("nan"))) for mark in marks))
    for low, high in ((0.0, 0.8), (0.8, 0.95), (0.95, 1.05), (1.05, 1.25), (1.25, 2.0), (2.0, math.inf)):
        share = sum(revenue for ratio, revenue, _g, _r in found if low <= ratio < high) / total
        print("   %.2f to %-5s %5.1f%% of revenue" % (low, "%.2f" % high, 100 * share))
    by_good = defaultdict(lambda: [0.0, 0.0])
    for ratio, revenue, good, _recipe in found:
        by_good[good][0] += revenue * ratio
        by_good[good][1] += revenue
    ranked = sorted(((value / weight, weight / total, good) for good, (value, weight) in by_good.items() if weight > 0.0), reverse=True)
    print("   furthest above cost: " + ", ".join("%s %.2f (%.1f%%)" % (good, ratio, 100 * share) for ratio, share, good in ranked[:8]))
    print("   furthest below cost: " + ", ".join("%s %.2f (%.1f%%)" % (good, ratio, 100 * share) for ratio, share, good in ranked[-8:]))


report("opening")
for year in range(years):
    economy.step(inputs)
    if year + 1 in (1, 2, 5, 10, 20, years):
        report("after year %d" % (year + 1))
