"""The first year's labour markets: hours offered, wanted and hired by work area and by trade, and the areas where employers want far
more hours than are offered. Usage: python3 first_year_labour_probe.py <civ>"""
import random, sys
import numpy as np
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.labour.market import clearing as clearing_module, clearing_tail
from sim.markets import port_sites

civ = sys.argv[1]
captured = []
original_clear = clearing_tail.clear_packed


def clear(state, packed, elasticity, search_share):
    result = original_clear(state, packed, elasticity, search_share)
    if not captured:
        print("packed attributes:", [name for name in dir(packed) if not name.startswith("_")][:40])
        print("result attributes:", [name for name in dir(result) if not name.startswith("_")][:40])
    captured.append((packed, result))
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
print("clearings in the year:", len(captured))
by_area, by_trade = {}, {}
for result in outcome_results if False else []:
    pass
ledger_results = getattr(economy, "_last_labour_results", None)
packed, result = captured[-1]
print("market_trade", type(packed.market_trade), list(packed.market_trade)[:3], "market_area", list(packed.market_area)[:3], "names", type(result.names), str(result.names)[:300])
area_names, trade_names = (list(result.names[0]), list(result.names[1])) if len(result.names) >= 2 else ([], [])
print("names lengths", [len(each) for each in result.names])
def named(names, code):
    return names[int(code)] if int(code) < len(names) else str(code)
keys = [(named(trade_names, trade), named(area_names, area)) for trade, area in zip(packed.market_trade, packed.market_area)]
if len(keys) != len(result.hours_offered):
    keys = [keys[index] for index in result.markets]
offered, wanted, hired, wage = result.hours_offered, result.hours_wanted, result.hours_hired, result.wage
print("totals: offered %.4g wanted %.4g hired %.4g" % (offered.sum(), wanted.sum(), hired.sum()))
if keys is not None:
    for index, key in enumerate(keys):
        trade, area = (key if isinstance(key, tuple) else str(key).split("|"))[:2]
        for table, name in ((by_area, area), (by_trade, trade)):
            row = table.setdefault(name, [0.0, 0.0, 0.0])
            row[0] += offered[index]; row[1] += wanted[index]; row[2] += hired[index]
    for title, table in (("by work area", by_area), ("by trade", by_trade)):
        print("--", title, "(offered, wanted, hired, wanted/offered)")
        for name, row in sorted(table.items(), key=lambda pair: -(pair[1][1] - pair[1][2]))[:14]:
            print("   %-32s %10.4g %10.4g %10.4g  %.2f" % (str(name)[:32], row[0], row[1], row[2], row[1] / max(row[0], 1e-9)))
print("-- trades in the tightest area and the two trades of interest by area (offered, wanted, hired)")
tight = max(by_area.items(), key=lambda pair: pair[1][1] / max(pair[1][0], 1e-9))[0]
for index, (trade, area) in enumerate(keys):
    if area == tight and (wanted[index] > 1e6 or offered[index] > 1e6):
        print("   %-18s %-24s %10.4g %10.4g %10.4g" % (trade, area, offered[index], wanted[index], hired[index]))
for index, (trade, area) in enumerate(keys):
    if trade in ("farmer", "labourer", "spinner") and area != tight:
        print("   %-18s %-24s %10.4g %10.4g %10.4g" % (trade, area, offered[index], wanted[index], hired[index]))
