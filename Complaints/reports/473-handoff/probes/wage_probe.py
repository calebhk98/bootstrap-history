"""One spin-up; for chosen labour markets print by year the head of the clearing (last wage, wage before the rounds, goal,
target, reservation, ceiling, hours offered) and the outcome (wage paid, hours wanted, hired), and the bids' caps.
Usage: python3 wage_probe.py <civ> <first_year> <last_year> <trade|area> [<trade|area> ...]"""
import random, sys
import numpy as np
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.labour.market import clearing as clearing_module, clearing_tail, clearing_kernel as kernel
from sim.markets import port_sites
from sim.markets.spin_up import spin_up_years

civ, first_year, last_year = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
chosen = sys.argv[4:]
current = [0]
original_clear = clearing_tail.clear_packed


def clear(state, packed, elasticity, search_share):
    last_wages = {}
    for market in chosen:
        trade, area = market.split("|")
        last_wages[market] = state.wages.get(area, {}).get(trade) if hasattr(state.wages, "get") else None
    result = original_clear(state, packed, elasticity, search_share)
    if first_year <= current[0] <= last_year:
        areas, trades = result.names
        for row in range(len(result)):
            name = "%s|%s" % (trades[result.trade[row]], areas[result.area[row]])
            if name not in chosen:
                continue
            market = result.markets[row]
            heads = packed_heads[0][market] if packed_heads[0] is not None else None
            low, high = result.bid_offsets[market], result.bid_offsets[market + 1]
            caps, hours = result.caps[low:high], result.bid_hours[low:high]
            order = np.argsort(-caps)
            total = hours.sum()
            cumulative = np.cumsum(hours[order])
            quantiles = [caps[order][min(len(order) - 1, int(np.searchsorted(cumulative, share * total)))] for share in (0.1, 0.25, 0.5, 0.75, 0.9)] if len(order) else []
            print("y%2d %-28s last %s | head wage %.4f goal %.4f target %.4f resv %.4f ceil %.4f offered %.4g | paid %.4f offered %.4g wanted %.4g hired %.4g | bid hours %.4g caps q10..q90 %s" % (
                current[0], name, "%.4f" % last_wages[name] if last_wages.get(name) is not None else "None",
                heads[kernel.HEAD_WAGE], heads[kernel.HEAD_GOAL], heads[kernel.HEAD_TARGET], heads[kernel.HEAD_RESERVATION], heads[kernel.HEAD_CEILING],
                heads[kernel.HEAD_OFFERED], result.wage[row], result.hours_offered[row], result.hours_wanted[row], result.hours_hired[row], total,
                " ".join("%.3f" % cap for cap in quantiles)), flush=True)
    return result


packed_heads = [None]
from sim.labour.market import clearing_arrays
original_heads = clearing_arrays.run_heads


def run_heads(packed):
    heads = original_heads(packed)
    packed_heads[0] = heads
    return heads


clearing_arrays.run_heads = run_heads
clearing_tail.clear_packed = clear
clearing_module.clearing_tail.clear_packed = clear

_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
first_years, trimmed_years = spin_up_years()
for year in range(min(last_year + 1, first_years)):
    current[0] = year
    economy.step(inputs)
