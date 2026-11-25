"""Scratch: the merchant's stock held for routes each year: how much the crew could carry, how much room the destinations have, how much is
offered where it stands; and the crew hours it wanted against those it hired. usage: civ_merchant_stuck.py <tree> <civ> <rule set> <years> <first>"""
import dataclasses, random, sys
tree, civ, rules_name, years, first = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
sys.path.insert(0, tree)
from sim.economy import api as economy_api
from sim.economy import rule_sets, merchants, year_order_sources
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import api as markets_api
from sim.markets import spin_up_stages as stages
state = {"year": -1}
rows = {}
real_rule = rule_sets.RULE_SETS[rules_name].merchant_stock_offered_where_it_stands
def logged(units_held, share_crewed, room):
    offered = real_rule(units_held, share_crewed, room)
    if state["year"] >= first:
        row = rows.setdefault(state["year"], {"stocks": 0, "held": 0.0, "crew_carries": 0.0, "room": 0.0, "offered": 0.0, "short_of_crew": 0.0, "short_of_room": 0.0})
        row["stocks"] += 1; row["held"] += units_held; row["offered"] += min(units_held, offered)
        row["stuck_stocks"] = row.get("stuck_stocks", 0) + (1 if offered > 0.0 else 0)
        by_crew = units_held * min(1.0, max(0.0, share_crewed))
        row["crew_carries"] += by_crew; row["room"] += min(room, units_held)
        if by_crew <= room:
            row["short_of_crew"] += units_held - by_crew
        else:
            row["short_of_room"] += units_held - max(0.0, room)
    return offered
rule_sets.RULE_SETS[rules_name] = dataclasses.replace(rule_sets.RULE_SETS[rules_name], merchant_stock_offered_where_it_stands=logged)
real_orders = merchants.orders
def orders(merchant, view, carriage, area_map, cash, held, *args, **kwargs):
    if state["year"] >= first:
        row = rows.setdefault(state["year"], {"stocks": 0, "held": 0.0, "crew_carries": 0.0, "room": 0.0, "offered": 0.0, "short_of_crew": 0.0, "short_of_room": 0.0})
        row["all_held"] = sum(held.values()); row["wanted_hours"] = sum((merchant.carriage_hours_wanted or {}).values())
        shares = kwargs.get("crewed_share_by_tile") or {}
        row["tiles"] = len(shares); row["least_share"] = min(shares.values()) if shares else -1; row["mean_share"] = sum(shares.values()) / len(shares) if shares else -1
    return real_orders(merchant, view, carriage, area_map, cash, held, *args, **kwargs)
merchants.orders = orders
import numpy as np
from sim.economy import merchants_plan, merchants_book_kernel as kernel
real_commit = kernel.commit_orders
class Proxy:
    def __getattr__(self, name):
        return getattr(kernel, name)
    def commit_orders(self, destinations, sources, outlays, remaining, *rest):
        quantities = real_commit(destinations, sources, outlays, remaining, *rest)
        if state["year"] >= first:
            row = rows.setdefault(state["year"], {"stocks": 0, "held": 0.0, "crew_carries": 0.0, "room": 0.0, "offered": 0.0, "short_of_crew": 0.0, "short_of_room": 0.0})
            row["committed"] = row.get("committed", 0.0) + float((quantities * outlays).sum())
            row["committed_rows"] = row.get("committed_rows", 0) + int((quantities > 0).sum())
        return quantities
merchants_plan.merchants_book_kernel = Proxy()
from sim.economy.order_rows import OrderRows
real_bid = OrderRows.bid
def bid(self, agent, good, area, tile, floor, quantity, price, *rest, **more):
    if state["year"] >= first and str(agent).startswith("merchant"):
        row = rows.setdefault(state["year"], {"stocks": 0, "held": 0.0, "crew_carries": 0.0, "room": 0.0, "offered": 0.0, "short_of_crew": 0.0, "short_of_room": 0.0})
        row["bid_value"] = row.get("bid_value", 0.0) + quantity * price
        row["bid_rows"] = row.get("bid_rows", 0) + 1
    return real_bid(self, agent, good, area, tile, floor, quantity, price, *rest, **more)
OrderRows.bid = bid
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ), cfg=markets_api.rule_set_configuration(rules_name))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
for year in range(years):
    state["year"] = year
    economy.step(stages.year_inputs(economy))
print("units, all goods summed (a rough size): year, all it holds, held for routes, crew carries, room for, offered where it stands (short of crew, short of room), crew hours wanted, tiles with a crew plan, least and mean share crewed")
for year in range(first, years):
    row = rows.get(year)
    if row:
        print("%4d held for routes %10.4g in %3d stocks, offered where it stands %10.4g in %3d stocks | cargo sized %10.4g in %3d rows, bids written %10.4g in %3d rows | least and mean share crewed %6.3f %6.3f" % (
              year, row["held"], row["stocks"], row["offered"], row.get("stuck_stocks", 0), row.get("committed", 0.0), row.get("committed_rows", 0), row.get("bid_value", 0.0), row.get("bid_rows", 0),
              row.get("least_share", -1), row.get("mean_share", -1)))
