"""Scratch: who holds a good, by kind of holder and year. usage: civ_land.py <tree> <civ> <rule set> <years> <first> <good>"""
import random, sys
tree, civ, rules_name, years, first, good = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
sys.path.insert(0, tree)
from sim.economy import api as economy_api
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import api as markets_api
from sim.markets import spin_up_stages as stages
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ), cfg=markets_api.rule_set_configuration(rules_name))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
rec = economy.record
def held():
    producers = set(rec.producers)
    totals = {"producers": 0.0, "households": 0.0, "others": 0.0}
    biggest = {}
    for agent in rec.book.holders_of(good):
        quantity = rec.book.holdings(agent)["goods"].get(good, 0.0)
        if isinstance(quantity, dict):
            quantity = sum(quantity.values())
        if not quantity:
            continue
        kind = "producers" if agent in producers else "households" if str(agent).startswith("household") else "others"
        totals[kind] += quantity
        if kind != "households":
            biggest[agent] = quantity
    return totals, biggest
before = None
for year in range(years):
    outcome = economy.step(stages.year_inputs(economy))
    if year >= first:
        totals, biggest = held()
        price = (getattr(outcome, "prices", None) or {}).get(good)
        print("%4d  producers %12.5g  households %12.5g  others %12.5g  price %s  producers holding %d" % (year, totals["producers"], totals["households"], totals["others"], price, sum(1 for agent in biggest if agent in set(rec.producers))))
        if before is not None:
            moved = sorted(((biggest.get(agent, 0.0) - before.get(agent, 0.0), agent) for agent in set(biggest) | set(before)), key=lambda item: -abs(item[0]))[:4]
            print("        largest changes: " + "; ".join("%s %+.4g" % (agent, change) for change, agent in moved if change))
        before = biggest
