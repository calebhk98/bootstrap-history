"""What each merchant expects of a good's price and volume in every area, by year, with the areas' cleared prices.
Usage: python3 merchant_beliefs_probe.py <civ> <years> <good> [<good> ...]"""
import random, sys
from sim.economy import api as economy_api
from sim.economy import merchants as merchants_module
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ, years, goods = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
area_map = setup.area_map()
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
print([name for name in dir(economy) if "view" in name or "area" in name or "carriage" in name][:30])
for year in range(years):
    outcome = economy.step(inputs)
    print("year", year)
    for key, merchant in economy.record.merchants.items():
        print("  ", key, "home", merchant.home_tile, "stretch", getattr(merchant, "stretch", None), "in transit", len(merchant.in_transit or ()),
              "expects %d prices, %d volumes" % (len(merchant.expected_prices), len(merchant.expected_volumes)))
        for good in goods:
            for area in area_map.areas(good):
                print("      %-12s %-14s expected price %s volume %s" % (good, area.area_id, merchant.expected_prices.get((good, area.area_id)),
                      merchant.expected_volumes.get((good, area.area_id))))
