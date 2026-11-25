"""Scratch: each merchant's cash and held stock when it orders, and what it bids and offers, by year.
usage: civ_merchant.py <tree> <civ> <rule set> <years> <first>"""
import os, random, sys
tree, civ, rules_name, years, first = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
sys.path.insert(0, tree)
from sim.economy import api as economy_api
from sim.economy import goods_clear_one_price as one_price, merchants
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import api as markets_api
from sim.markets import spin_up_stages as stages
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ), cfg=markets_api.rule_set_configuration(rules_name))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
if os.environ.get("MEMBER"):
    from sim.markets.spin_up_ensemble import perturb_household_cash, cash_factor
    perturb_household_cash(economy, cash_factor(int(os.environ["MEMBER"])))
state = {"year": -1}
rows = {}
real_orders = merchants.orders
def orders(merchant, view, carriage, area_map, cash, held, *args, **kwargs):
    if state["year"] >= first:
        value = 0.0
        for (good, tile), quantity in held.items():
            price = view.price(good, area_map.area_of(good, tile))
            value += quantity * (price or 0.0)
        row = rows.setdefault(state["year"], {"cash": 0.0, "held": 0.0, "bid": 0.0, "bought": 0.0, "offered": 0.0, "sold": 0.0})
        row["cash"] += cash; row["held"] += value
    return real_orders(merchant, view, carriage, area_map, cash, held, *args, **kwargs)
merchants.orders = orders
real = one_price.at_one_price
def probe(context, good, area, last_price, bids, offers):
    out = real(context, good, area, last_price, bids, offers)
    if state["year"] >= first:
        row = rows.setdefault(state["year"], {"cash": 0.0, "held": 0.0, "bid": 0.0, "bought": 0.0, "offered": 0.0, "sold": 0.0})
        result = out[1]
        price = result.price or last_price or 0.0
        for bid in bids:
            if str(bid.buyer).startswith("merchant"):
                row["bid"] += bid.budget
        for offer in offers:
            if str(offer.seller).startswith("merchant"):
                row["offered"] += offer.quantity * price
    return out
one_price.at_one_price = probe
for year in range(years):
    state["year"] = year
    economy.step(stages.year_inputs(economy))
print("%4s %12s %12s %12s %12s" % ("year", "cash", "held value", "bid budgets", "offered value"))
for year in range(first, years):
    row = rows.get(year)
    if row:
        print("%4d %12.5g %12.5g %12.5g %12.5g" % (year, row["cash"], row["held"], row["bid"], row["offered"]))
