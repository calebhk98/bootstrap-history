"""Scratch: some goods' bids by year, summed over areas. usage: civ_good_bids.py <tree> <civ> <rule set> <years> <first> <good,good>"""
import random, sys
tree, civ, rules_name, years, first, goods = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6].split(",")
sys.path.insert(0, tree)
from sim.economy import api as economy_api
from sim.economy import goods_clear_one_price as one_price
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import api as markets_api
from sim.markets import spin_up_stages as stages
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ), cfg=markets_api.rule_set_configuration(rules_name))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
import os
if os.environ.get("MEMBER"):
    from sim.markets.spin_up_ensemble import perturb_household_cash, cash_factor
    perturb_household_cash(economy, cash_factor(int(os.environ["MEMBER"])))
state = {"year": -1}
table = {}
real = one_price.at_one_price
def probe(context, good, area, last_price, bids, offers):
    out = real(context, good, area, last_price, bids, offers)
    if state["year"] >= first and good in goods:
        result = out[1]
        row = table.setdefault((state["year"], good), {"floor": 0.0, "flex": 0.0, "budget": 0.0, "other": 0.0, "sold": 0.0, "value": 0.0, "last": 0.0, "weight": 0.0, "offered": 0.0})
        for bid in bids:
            if bid.buyer.startswith("household"):
                row["floor"] += bid.floor_quantity; row["flex"] += bid.flexible_quantity; row["budget"] += bid.budget
                key = "p%s" % getattr(bid, "priority", "?")
                row[key] = row.get(key, 0.0) + bid.budget
            else:
                row["other"] += bid.floor_quantity + bid.flexible_quantity
        row["sold"] += result.quantity
        row["value"] += result.quantity * (result.price or 0.0)
        row["offered"] += sum(offer.quantity for offer in offers)
        row["last"] += (last_price or 0.0) * result.quantity; row["weight"] += result.quantity
    return out
one_price.at_one_price = probe
for year in range(years):
    state["year"] = year
    economy.step(stages.year_inputs(economy))
for good in goods:
    print(good)
    print("  %4s %10s %10s %10s %10s %10s %10s %9s %9s" % ("year", "hh floor", "hh flex", "hh budget", "others", "offered", "sold", "last", "cleared"))
    for year in range(first, years):
        row = table.get((year, good))
        if row:
            print("  %4d %10.4g %10.4g %10.4g %10.4g %10.4g %10.4g %9.4g %9.4g" % (year, row["floor"], row["flex"], row["budget"], row["other"], row["offered"], row["sold"],
                  row["last"] / row["weight"] if row["weight"] > 0 else -1, row["value"] / row["sold"] if row["sold"] > 0 else -1),
                  " | budget by priority: " + " ".join("%s %.4g" % (k, v) for k, v in sorted(row.items()) if k.startswith("p")))
