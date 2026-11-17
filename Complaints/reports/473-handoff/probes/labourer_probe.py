"""One labour market in the first year: every employer's bid (hours, wage limit) against the hours it was given.
Usage: python3 labourer_probe.py <civ> <trade> <work area>"""
import random, sys
import numpy as np
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.labour.market import clearing as clearing_module, clearing_tail
from sim.markets import port_sites

civ, trade, area = sys.argv[1], sys.argv[2], sys.argv[3]
captured = []
original_clear = clearing_tail.clear_packed
def clear(state, packed, elasticity, search_share):
    result = original_clear(state, packed, elasticity, search_share)
    captured.append((state, packed, result))
    return result
clearing_tail.clear_packed = clear
clearing_module.clearing_tail.clear_packed = clear
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
outcome = economy.step(inputs)
state, packed, result = captured[-1]
for name in ("heads", "caps", "bid_employer", "bid_hours", "bid_offsets", "index", "markets", "arguments"):
    value = getattr(packed, name, None)
    print("packed.%s" % name, type(value).__name__, getattr(value, "shape", None) or (len(value) if hasattr(value, "__len__") else ""), getattr(value, "dtype", ""))
for name in ("hired_by_employer", "employers", "demand", "hours_held", "clearing", "caps", "bid_hours", "bid_offsets", "wage", "names", "markets"):
    value = getattr(result, name, None)
    print("result.%s" % name, type(value).__name__, getattr(value, "shape", None) or (len(value) if hasattr(value, "__len__") else ""), getattr(value, "dtype", ""))
area_names, trade_names = list(result.names[0]), list(result.names[1])
keys = [(trade_names[int(t)], area_names[int(a)]) for t, a in zip(packed.market_trade, packed.market_area)]
place = keys.index((trade, area))
print("market", place, keys[place], "offered %.4g wanted %.4g hired %.4g wage %.4g" % (result.hours_offered[place], result.hours_wanted[place], result.hours_hired[place], result.wage[place]))
start, end = int(packed.bid_offsets[place]), int(packed.bid_offsets[place + 1])
print("bids", start, end)
employers = result.employers
caps = np.asarray(packed.caps)
bid_hours = np.asarray(packed.bid_hours)
wage = result.wage[place]
try:
    hired = result.hired_by_employer(place)
except TypeError:
    hired = result.hired_by_employer()
print("hired_by_employer returns", type(hired).__name__, (list(hired.items())[:3] if isinstance(hired, dict) else str(hired)[:200]))
by_employer = {}
for bid in range(start, end):
    row = by_employer.setdefault(employers[int(packed.bid_employer[bid])], [0.0, 0.0, []])
    row[0] += bid_hours[bid]
    if caps[bid] >= wage: row[1] += bid_hours[bid]
    row[2].append((round(float(bid_hours[bid]), 1), round(float(caps[bid]), 3)))
print("wage", wage, "hours bid %.4g, of which with a cap at or above the wage %.4g" % (sum(r[0] for r in by_employer.values()), sum(r[1] for r in by_employer.values())))
for name, row in sorted(by_employer.items(), key=lambda pair: -(pair[1][0] - pair[1][1]))[:22]:
    got = hired.get(name) if isinstance(hired, dict) else None
    print("   %-44s bid %10.4g  payable %10.4g  hired %s  tiers %s" % (name[:44], row[0], row[1], ("%.4g" % got) if got is not None else "?", row[2]))
