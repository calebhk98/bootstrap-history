"""Scratch: a good's bids and offers by kind of agent and year, with the largest non-household buyers and the sellers.
usage: civ_good_others.py <tree> <civ> <rule set> <years> <first> <good>   (MEMBER env: the ensemble member)"""
import os, random, sys
tree, civ, rules_name, years, first, good_asked = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
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
if os.environ.get("MEMBER"):
    from sim.markets.spin_up_ensemble import perturb_household_cash, cash_factor
    perturb_household_cash(economy, cash_factor(int(os.environ["MEMBER"])))
state = {"year": -1}
table = {}
real = one_price.at_one_price
def kind_of(agent):
    text = str(agent)
    return text.split(":", 1)[0] if ":" in text else text.split("_", 1)[0]
def probe(context, good, area, last_price, bids, offers):
    out = real(context, good, area, last_price, bids, offers)
    if state["year"] >= first and good == good_asked:
        row = table.setdefault(state["year"], {"bid": {}, "budget": {}, "offer": {}, "buyers": {}, "sellers": {}, "sold": 0.0, "value": 0.0})
        for bid in bids:
            kind = kind_of(bid.buyer)
            quantity = bid.floor_quantity + bid.flexible_quantity
            row["bid"][kind] = row["bid"].get(kind, 0.0) + quantity
            row["budget"][kind] = row["budget"].get(kind, 0.0) + bid.budget
            if kind != "household":
                row["buyers"][bid.buyer] = row["buyers"].get(bid.buyer, 0.0) + quantity
        for offer in offers:
            kind = kind_of(offer.seller)
            row["offer"][kind] = row["offer"].get(kind, 0.0) + offer.quantity
            row["sellers"][offer.seller] = row["sellers"].get(offer.seller, 0.0) + offer.quantity
        result = out[1]
        row["sold"] += result.quantity
        row["value"] += result.quantity * (result.price or 0.0)
    return out
one_price.at_one_price = probe
for year in range(years):
    state["year"] = year
    economy.step(stages.year_inputs(economy))
for year in range(first, years):
    row = table.get(year)
    if not row:
        continue
    print("%4d sold %.4g at %.4g" % (year, row["sold"], row["value"] / row["sold"] if row["sold"] > 0 else -1))
    print("     bids by kind (quantity, budget): " + "; ".join("%s %.4g, %.4g" % (kind, quantity, row["budget"][kind]) for kind, quantity in sorted(row["bid"].items())))
    print("     offers by kind: " + "; ".join("%s %.4g" % item for item in sorted(row["offer"].items())))
    print("     largest other buyers: " + "; ".join("%s %.4g" % (agent, quantity) for agent, quantity in sorted(row["buyers"].items(), key=lambda item: -item[1])[:5]))
    print("     largest sellers: " + "; ".join("%s %.4g" % (agent, quantity) for agent, quantity in sorted(row["sellers"].items(), key=lambda item: -item[1])[:5]))
