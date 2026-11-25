"""Scratch: which goods' household budgets alternate from year to year. usage: civ_alt.py <tree> <civ> <rule set> <years> <first>"""
import random, sys
tree, civ, rules_name, years, first = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
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
state = {"year": -1}
budget, paid, price = {}, {}, {}
real = one_price.at_one_price
def probe(context, good, area, last_price, bids, offers):
    out = real(context, good, area, last_price, bids, offers)
    year = state["year"]
    if year >= first:
        result = out[1]
        asked = sum(bid.budget for bid in bids if bid.buyer.startswith("household"))
        wanted = sum(bid.floor_quantity + bid.flexible_quantity for bid in bids)
        budget.setdefault(good, {}); paid.setdefault(good, {}); price.setdefault(good, {})
        budget[good][year] = budget[good].get(year, 0.0) + asked
        paid[good][year] = paid[good].get(year, 0.0) + result.quantity * (result.price or 0.0)
        price[good][year] = result.price or price[good].get(year, 0.0)
    return out
one_price.at_one_price = probe
for year in range(years):
    state["year"] = year
    economy.step(stages.year_inputs(economy))
span = list(range(first, years))
def swing(series):
    odd = [series.get(y, 0.0) for y in span if y % 2 == 1]; even = [series.get(y, 0.0) for y in span if y % 2 == 0]
    return sum(odd) / len(odd) - sum(even) / len(even)
print("goods by the size of the odd-year less even-year household budget; then each year's budget")
for good in sorted(budget, key=lambda g: -abs(swing(budget[g])))[:22]:
    print("%-22s %+10.3g | %s" % (good[:22], swing(budget[good]), " ".join("%9.4g" % budget[good].get(y, 0.0) for y in span)))
print("money paid in the market (all buyers), same order by its own swing")
for good in sorted(paid, key=lambda g: -abs(swing(paid[g])))[:22]:
    print("%-22s %+10.3g | %s" % (good[:22], swing(paid[good]), " ".join("%9.4g" % paid[good].get(y, 0.0) for y in span)))
