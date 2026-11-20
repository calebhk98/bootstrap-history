"""Twin probe of the labour hiring kernel in one year: captures what goes into `hiring_kernel.hire_markets` and what
comes out of it and of `finish_markets`, in each twin, and prints the markets where they differ.

Usage: python3 hire_probe.py <civ> <eps> <watch_year>
"""
import random
import sys

import numpy as np

from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.labour.market import clearing_tail, hiring_kernel
from sim.markets import port_sites
from sim.markets.spin_up_ensemble import perturb_household_cash

civ, eps, watch_year = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
captures = [[], []]
active = [None]
original_hire = hiring_kernel.hire_markets
original_finish = clearing_tail.kernel.finish_markets
original_clear = clearing_tail.clear_packed


def hire(offsets, hired, kept, wanted, offers, ceilings, pools, asks, floors, has_job, taken_amount, taken_flag, *rest):
    before = {"offsets": offsets.copy(), "hired": hired.copy(), "kept": kept.copy(), "wanted": wanted.copy(), "offers": offers.copy(),
              "ceilings": ceilings.copy(), "pools": pools.copy(), "asks": asks.copy(), "floors": floors.copy(), "has_job": has_job.copy()}
    original_hire(offsets, hired, kept, wanted, offers, ceilings, pools, asks, floors, has_job, taken_amount, taken_flag, *rest)
    if active[0] is not None:
        before.update({"hired_after": hired.copy(), "offers_after": offers.copy(), "taken": taken_amount.copy()})
        captures[active[0]].append(before)


class HiringStandIn:
    hire_markets = staticmethod(hire)


clearing_tail.hiring_kernel = HiringStandIn
real_kernel = clearing_tail.kernel


def finish(*args):
    result = real_kernel.finish_markets(*args)
    if active[0] is not None:
        captures[active[0]][-1]["rank"] = args[10].copy()
        captures[active[0]][-1]["hired_final"] = args[11].copy()
        captures[active[0]][-1]["slot_offsets"] = args[8].copy()
    return result


class TailStandIn:
    count_slots = staticmethod(real_kernel.count_slots)
    fill_slots = staticmethod(real_kernel.fill_slots)
    finish_markets = staticmethod(finish)


clearing_tail.kernel = TailStandIn


def clear(state, packed, elasticity, search_share):
    result = original_clear(state, packed, elasticity, search_share)
    if active[0] is not None:
        capture = captures[active[0]][-1]
        capture["areas"] = [state.ids.areas.names[number] for number in packed.market_area]
        capture["trades"] = [state.ids.trades.names[number] for number in packed.market_trade]
        capture["employers"] = list(state.ids.employers.table.names)
        capture["slot_employer"] = None
        capture["result"] = result
    return result


clearing_tail.clear_packed = clear
from sim.labour.market import clearing as clearing_module
clearing_module.clearing_tail.clear_packed = clear

_tree, _prices, nodes, _wages, _goods = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
twins = []
for factor in (1.0, 1.0 + eps):
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    if factor != 1.0:
        perturb_household_cash(economy, factor)
    twins.append(economy)
inputs = [EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
          for economy in twins]
for year in range(watch_year + 1):
    for number, (economy, year_inputs) in enumerate(zip(twins, inputs)):
        active[0] = number if year == watch_year else None
        economy.step(year_inputs)
        active[0] = None

first, second = captures[0][-1], captures[1][-1]
print("calls captured", len(captures[0]), len(captures[1]), "markets", len(first["offsets"]) - 1, len(second["offsets"]) - 1)
same_shape = np.array_equal(first["offsets"], second["offsets"])
print("same slot layout:", same_shape)


def relative(a, b):
    scale = np.maximum(np.abs(a), np.abs(b))
    return np.where(scale > 0, np.abs(a - b) / np.where(scale > 0, scale, 1.0), 0.0)


if same_shape:
    for name in ("hired", "kept", "wanted", "offers", "ceilings", "hired_after", "offers_after", "taken"):
        difference = relative(first[name], second[name])
        print("  slots %-13s largest relative difference %.3g (of %d)" % (name, difference.max() if len(difference) else 0.0, len(difference)))
    for name in ("pools", "asks", "floors"):
        difference = relative(first[name], second[name])
        print("  market %-12s largest relative difference %.3g" % (name, difference.max()))
    offsets = first["offsets"]
    difference = relative(first["hired_after"], second["hired_after"])
    for market in range(len(offsets) - 1):
        low, high = offsets[market], offsets[market + 1]
        if high > low and difference[low:high].max() > 1e-4:
            print("== market", first["areas"][market] if "areas" in first else market, first["trades"][market] if "trades" in first else "",
                  "pool %.9g ask %.12g floor %.12g" % (first["pools"][market], first["asks"][market], first["floors"][market]))
            for slot in range(low, high):
                print("     slot %d wanted %.9g kept %.9g hired_before %.9g offer %.15g ceiling %.15g | A hired %.9g offer_after %.12g | B hired %.9g offer_after %.12g | in-diff w %.2g o %.2g c %.2g" % (
                    slot - low, first["wanted"][slot], first["kept"][slot], first["hired"][slot], first["offers"][slot], first["ceilings"][slot],
                    first["hired_after"][slot], first["offers_after"][slot], second["hired_after"][slot], second["offers_after"][slot],
                    relative(first["wanted"][slot:slot + 1], second["wanted"][slot:slot + 1])[0],
                    relative(first["offers"][slot:slot + 1], second["offers"][slot:slot + 1])[0],
                    relative(first["ceilings"][slot:slot + 1], second["ceilings"][slot:slot + 1])[0]))

print("---- after finish_markets (poaching) ----")
final_a, final_b = first.get("hired_final"), second.get("hired_final")
if final_a is not None and same_shape:
    difference = relative(final_a, final_b)
    print("  slots hired after finish: largest relative difference %.3g" % difference.max())
    offsets = first["offsets"]
    result_a, result_b = first["result"], second["result"]
    shown = 0
    for market in range(len(offsets) - 1):
        low, high = offsets[market], offsets[market + 1]
        if high > low and difference[low:high].max() > 1e-3 and shown < 3:
            shown += 1
            print("== market", first["areas"][market], first["trades"][market], "pool %.9g" % first["pools"][market],
                  "sum hired after rounds A %.9g B %.9g; after finish A %.9g B %.9g" % (
                      first["hired_after"][low:high].sum(), second["hired_after"][low:high].sum(), final_a[low:high].sum(), final_b[low:high].sum()))
            ranks = None
            for slot in range(low, high):
                print("     slot %2d rank A %.15g B %.15g wanted %.8g | after rounds A %.8g B %.8g | after finish A %.8g B %.8g" % (
                    slot - low, first["rank"][slot], second["rank"][slot], first["wanted"][slot], first["hired_after"][slot],
                    second["hired_after"][slot], final_a[slot], final_b[slot]))
