"""One spin-up; per year the labour markets' totals: hours offered, wanted, hired; hours in markets with excess supply and
with excess demand; the hours-weighted wage and reservation. Usage: python3 labour_totals_probe.py <civ> [first] [trimmed]"""
import random, sys
import numpy as np
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.labour.market import clearing as clearing_module, clearing_tail, clearing_kernel as kernel, clearing_arrays
from sim.markets import port_sites
from sim.markets.spin_up import spin_up_years

civ = sys.argv[1]
first_years, trimmed_years = spin_up_years()
if len(sys.argv) > 2:
    first_years, trimmed_years = int(sys.argv[2]), int(sys.argv[3])
rows = []
packed_heads = [None]
original_heads = clearing_arrays.run_heads
original_clear = clearing_tail.clear_packed


def run_heads(packed):
    packed_heads[0] = original_heads(packed)
    return packed_heads[0]


def clear(state, packed, elasticity, search_share):
    result = original_clear(state, packed, elasticity, search_share)
    offered, wanted, hired, wage = result.hours_offered, result.hours_wanted, result.hours_hired, result.wage
    heads = packed_heads[0][result.markets]
    reservation = heads[:, kernel.HEAD_RESERVATION]
    slack = offered > wanted * 1.02
    tight = wanted > offered * 1.02
    total = offered.sum()
    rows.append({"offered": total, "wanted": wanted.sum(), "hired": hired.sum(), "slack_offered": offered[slack].sum(),
                 "tight_offered": offered[tight].sum(), "wage": float((wage * hired).sum() / max(hired.sum(), 1e-9)),
                 "reservation": float((reservation * offered).sum() / max(total, 1e-9)),
                 "wage_over_reservation_slack": float((wage[slack] * offered[slack]).sum() / max((reservation[slack] * offered[slack]).sum(), 1e-9)) if slack.any() else float("nan")})
    return result


clearing_arrays.run_heads = run_heads
clearing_tail.clear_packed = clear
clearing_module.clearing_tail.clear_packed = clear
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
print("stage yr   offered    wanted     hired  hired/off  slack-share tight-share   wage  resv  wage/resv(slack)  price level")
for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
    if stage == "trimmed":
        economy_api.trim_workforce_to_expected_hours(economy)
    for year in range(years):
        outcome = economy.step(inputs)
        row = rows[-1]
        print("%-7s %2d %9.4g %9.4g %9.4g   %.3f      %.3f       %.3f    %.3f %.3f   %.2f           %.4f" % (
            stage, year, row["offered"], row["wanted"], row["hired"], row["hired"] / row["offered"], row["slack_offered"] / row["offered"],
            row["tight_offered"] / row["offered"], row["wage"], row["reservation"], row["wage_over_reservation_slack"], outcome.basket_price_level), flush=True)
