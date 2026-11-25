"""Scratch: what limits the merchant's new cargo each year: its candidate rows, the coin for them, the room they have, what it commits.
usage: civ_merchant_limits.py <tree> <civ> <rule set> <years> <first>"""
import random, sys
import numpy as np
tree, civ, rules_name, years, first = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
sys.path.insert(0, tree)
from sim.economy import api as economy_api
from sim.economy import merchants_plan, merchants_book_kernel as kernel
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import api as markets_api
from sim.markets import spin_up_stages as stages
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ), cfg=markets_api.rule_set_configuration(rules_name))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
state = {"year": -1}
real_commit = kernel.commit_orders
class Proxy:
    def __getattr__(self, name):
        return getattr(kernel, name)
    def commit_orders(self, destinations, sources, outlays, remaining, volumes, held, own_into, group_into, group_out, own_share, group_share, source_share):
        rooms = kernel.rooms_of(destinations, sources, volumes, held, own_into.copy(), group_into.copy(), group_out.copy(), own_share, group_share, source_share)
        quantities = real_commit(destinations, sources, outlays, remaining, volumes, held, own_into, group_into, group_out, own_share, group_share, source_share)
        if state["year"] >= first:
            spent = float((quantities * outlays).sum())
            room_value = float((rooms * outlays).sum())
            dest_limited = 0.0
            for row in range(len(rooms)):
                into = volumes[destinations[row]]
                if not np.isnan(into):
                    mine = own_share * into - held[destinations[row]]
                    if mine <= 0.0:
                        dest_limited += 1
            print("%4d rows %4d  coin for cargo %10.4g  room at first sight (value) %10.4g  rows whose destination share is full %4d  committed %10.4g  rows committed %d" % (
                state["year"], len(rooms), remaining, room_value, dest_limited, spent, int((quantities > 0).sum())))
        return quantities
merchants_plan.merchants_book_kernel = Proxy()
for year in range(years):
    state["year"] = year
    economy.step(stages.year_inputs(economy))
