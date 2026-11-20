"""Each area's market for chosen goods by year: delivered, unsold, unmet, the remembered price, its kind and the offered price.
Usage: python3 market_state_probe.py <civ> <years> <good> [<good> ...]"""
import random, sys
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.economy.market_memory import market_key
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
record = economy.record
for year in range(years):
    economy.step(inputs)
    print("year", year)
    for good in goods:
        for area in area_map.areas(good):
            key = market_key(good, area.area_id)
            print("   %-10s %-14s delivered %10.4g unsold %10.4g unmet %10.4g price %s kind %s offered %s" % (
                good, area.area_id, record.goods.volumes.get(key, 0.0) or 0.0, record.goods.unsold.get(key, 0.0) or 0.0,
                record.goods.unmet.get(key, 0.0) or 0.0, record.memory.prices.get(key), record.memory.price_kind(key), record.memory.offered_price(key)))
