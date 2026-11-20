"""The watched goods of a civilisation's opening and each one's share of the spending on them, as JSON (for
ensemble_moves.py on files written before the rows carried the shares). Usage: python3 watched_weights_probe.py <civ> <out.json>"""
import json, random, sys
from sim.economy import api as economy_api
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets.spin_up_year import watched_goods, watched_shares

civ, out = sys.argv[1], sys.argv[2]
_tree, _prices, nodes, _wages, _goods = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
economy = economy_api.blank_economy(game.view("agent_opening_setup")())
shares = watched_shares(economy, watched_goods(economy))
json.dump(shares, open(out, "w"))
for good, share in sorted(shares.items(), key=lambda pair: -pair[1]):
    print("%-28s %.4f" % (good, share))
