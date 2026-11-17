"""What households bid for the tools their own plots wear, year by year: quantity and coin by good, against what they hold and
what the year's makers were sized to sell. Usage: python3 tool_bids_probe.py <civ> [years]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, tool_wear, year_order_sources
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ = sys.argv[1]
years = int(sys.argv[2]) if len(sys.argv) > 2 else 2
tally = defaultdict(lambda: [0.0, 0.0, 0.0])
original = tool_wear.tool_bids
def tool_bids(buyer, tile, area_of, price_of, held_of, recipes, hours_by_recipe, specs, cash):
    bids = original(buyer, tile, area_of, price_of, held_of, recipes, hours_by_recipe, specs, cash)
    for bid in bids:
        row = tally[bid.good]
        row[0] += bid.floor_quantity + bid.flexible_quantity
        row[1] += bid.budget
        row[2] += held_of(bid.good)
    return bids
tool_wear.tool_bids = tool_bids
year_order_sources.tool_wear.tool_bids = tool_bids
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
sized = defaultdict(float)
for producer in economy.record.producers.values():
    recipe = setup.recipes[producer.recipe_id]
    for good, quantity in recipe.outputs.items():
        sized[good] += producer.expected_sales * producer.yield_factor * quantity
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
for year in range(years):
    tally.clear()
    outcome = economy.step(inputs)
    print("year", year, "households' tool bids: good, quantity bid, coin, held before, what the opening's makers were sized to sell a year, life")
    for good, (quantity, coin, held) in sorted(tally.items(), key=lambda pair: -pair[1][1]):
        print("   %-22s %10.4g %10.4g %10.4g %10.4g  %s" % (good, quantity, coin, held, sized.get(good, 0.0), setup.specs[good].service_life_years))
