"""Scratch: the merchant's crew hours each year when it sizes new cargo: hired, left free by the stocks kept, needed by the cargo sized,
and which crew keys are short. usage: civ_merchant_crew.py <tree> <civ> <rule set> <years> <first>"""
import dataclasses, random, sys
tree, civ, rules_name, years, first = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
sys.path.insert(0, tree)
from sim.economy import api as economy_api
from sim.economy import rule_sets, merchants
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import api as markets_api
from sim.markets import spin_up_stages as stages
state = {"year": -1, "hired": None, "plan": None}
real_rule = rule_sets.RULE_SETS[rules_name].merchant_cargo_the_crew_carries
def logged(rows, hours_by_row, hours_left):
    shares = real_rule(rows, hours_by_row, hours_left)
    if state["year"] >= first:
        left = hours_left()
        needed = hours_by_row()
        totals = {}
        for by_key in needed:
            for key, hours in by_key.items():
                totals[key] = totals.get(key, 0.0) + hours
        hired = state["hired"] or {}
        plan = state["plan"] or {}
        absent = {key: hours for key, hours in totals.items() if left is not None and key not in left}
        short = {key: (hours, left[key]) for key, hours in totals.items() if left is not None and key in left and hours > left[key]}
        print("%4d plan %.4g h in %d keys, hired %.4g h, left free %s h | cargo sized needs %.4g h in %d keys: %.4g h on %d keys the plan lacks, %.4g h on %d keys short (those have %.4g h free) | rows %d, whole %d, none %d" % (
            state["year"], sum(plan.values()), len(plan), sum(hired.values()), "none" if left is None else "%.4g" % sum(left.values()),
            sum(totals.values()), len(totals), sum(absent.values()), len(absent), sum(hours for hours, _free in short.values()), len(short), sum(free for _hours, free in short.values()),
            rows, sum(1 for share in shares if share >= 1.0), sum(1 for share in shares if share <= 0.0)))
        worst = sorted(short.items(), key=lambda item: -(item[1][0] - item[1][1]))[:4]
        print("       shortest keys (needed, free, hired, planned): " + "; ".join("%s %.3g %.3g %.3g %.3g" % (key, hours, free, hired.get(key, 0.0), plan.get(key, 0.0)) for key, (hours, free) in worst))
        missing = sorted(absent.items(), key=lambda item: -item[1])[:4]
        print("       largest keys the plan lacks: " + "; ".join("%s %.3g" % item for item in missing))
    return shares
rule_sets.RULE_SETS[rules_name] = dataclasses.replace(rule_sets.RULE_SETS[rules_name], merchant_cargo_the_crew_carries=logged)
real_orders = merchants.orders
def orders(merchant, *args, **kwargs):
    state["hired"] = kwargs.get("crew_hours_hired")
    state["plan"] = dict(merchant.carriage_hours_wanted or {})
    return real_orders(merchant, *args, **kwargs)
merchants.orders = orders
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ), cfg=markets_api.rule_set_configuration(rules_name))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
for year in range(years):
    state["year"] = year
    economy.step(stages.year_inputs(economy))
