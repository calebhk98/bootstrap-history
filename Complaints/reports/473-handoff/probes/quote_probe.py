"""For the markets of chosen goods that had bids and nothing on offer: the making cost, the best unfilled bid and the signal
the memory moves toward, by year. Usage: python3 quote_probe.py <civ> <years> <good> [<good> ...]"""
import random, sys
import numpy
from sim.economy import api as economy_api, year_remember
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages

civ, years, goods = sys.argv[1], int(sys.argv[2]), set(sys.argv[3:])
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = spin_up_stages.year_inputs(economy)
seen = {}
original_signals = year_remember.kernel.signals
original_remember = year_remember.remember_markets

class Wrapped:
    def __getattr__(self, name):
        return getattr(original_kernel, name)
    def signals(self, old, was_quote, usual, idle, total, received, wanted_old, quote_price, quote_kind, has_bids, offers_left, cost, funded, best, *rest):
        answer = original_signals(old, was_quote, usual, idle, total, received, wanted_old, quote_price, quote_kind, has_bids, offers_left, cost, funded, best, *rest)
        seen["arrays"] = (numpy.array(old), numpy.array(total), numpy.array(has_bids), numpy.array(offers_left), numpy.array(cost), numpy.array(funded),
                          numpy.array(best), numpy.array(wanted_old), answer[0].copy(), answer[1].copy())
        return answer

original_kernel = year_remember.kernel
year_remember.kernel = Wrapped()

def remember(setup_, record, keys, *rest):
    answer = original_remember(setup_, record, keys, *rest)
    old, total, has_bids, offers_left, cost, funded, best, wanted_old, signal, kind = seen["arrays"]
    for place, (good, area) in enumerate(keys):
        if good in goods and has_bids[place] and offers_left[place] == 0 and total[place] <= 0.0:
            print("   %-10s %-14s old %.3f cost %.3f best bid %.3f funded %s wanted at old %.4g -> signal %.3f kind %d" % (
                good, area, old[place], cost[place], best[place], bool(funded[place]), wanted_old[place], signal[place], kind[place]))
    return answer

year_remember.remember_markets = remember
import sim.economy.year_goods as year_goods
for module in (year_goods,):
    if hasattr(module, "remember_markets"):
        module.remember_markets = remember
for year in range(years):
    print("year", year)
    economy.step(inputs)
