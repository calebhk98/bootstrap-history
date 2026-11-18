"""Who got a good in the first year against what the opening sized: the units its makers were sized to make and made, the
units the producers that use it as an input were sized to take and got (by recipe), what its makers were left holding, and
the rest (households, merchants, anyone else); with the good's price after the year over its opening price.
Usage: python3 first_year_takers_probe.py <civ> <good> [<good> ...]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ, goods = sys.argv[1], sys.argv[2:]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
record = economy.record
book = record.book
before = {}
for key, producer in record.producers.items():
    recipe = setup.recipes[producer.recipe_id]
    before[key] = (producer.recipe_id, producer.expected_sales, producer.tile, producer.yield_factor,
                   {good: book.stock(producer.agent_id, good, producer.tile) for good in set(recipe.inputs) | set(recipe.outputs)})
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
economy.step(inputs)
view = economy.view()
for good in goods:
    sized_made = made = left = 0.0
    sized_take, got = defaultdict(float), defaultdict(float)
    price_now, price_weight = 0.0, 0.0
    for key, (recipe_id, sized, tile, yield_factor, held) in before.items():
        producer = record.producers.get(key)
        if producer is None:
            continue
        recipe = setup.recipes[recipe_id]
        worked = max(0.0, producer.last_runs or 0.0)
        if good in recipe.outputs:
            sized_made += recipe.outputs[good] * yield_factor * sized
            made += recipe.outputs[good] * yield_factor * worked
            left += max(0.0, book.stock(producer.agent_id, good, tile) - recipe.inputs.get(good, 0.0) * producer.capacity_runs)
            price = view.price(good, economy.area_map.area_of(good, tile))
            if price is not None:
                price_now += price * worked
                price_weight += worked
        if good in recipe.inputs and good not in recipe.outputs:
            per_run = recipe.inputs[good]
            sized_take[recipe_id] += per_run * sized
            got[recipe_id] += max(0.0, book.stock(producer.agent_id, good, tile) - held[good] + per_run * worked)
    base = sized_made or 1.0
    opening_price = setup.opening_prices.get(good)
    print("%s: makers sized for %.4g, made %.2f of it; left with its makers %.2f; price after the year %s of the opening's" % (
        good, sized_made, made / base, left / base,
        "%.2f" % (price_now / price_weight / opening_price) if price_weight and opening_price else "?"))
    taken = sum(got.values())
    print("   producers were sized to take %.2f of what was sized and got %.2f; everyone else was sized for %.2f and got %.2f" % (
        sum(sized_take.values()) / base, taken / base, 1.0 - sum(sized_take.values()) / base, (made - left - taken) / base))
    for recipe_id in sorted(sized_take, key=lambda each: -sized_take[each])[:8]:
        print("      %-30s sized to take %.3f, got %.3f" % (recipe_id[:30], sized_take[recipe_id] / base, got[recipe_id] / base))
