"""The households' year in money: what all cohorts received, what they spent, their coin before and after, and the producers'
coin, year by year, read where the year's close hands the cohorts their income and spending (`closed_scalars_of`).
Usage: python3 household_accounts_probe.py <civ> <years>"""
import random, sys
import numpy as np
from sim.economy import api as economy_api
from sim.economy import households_close_figures, economy as economy_module
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ, years = sys.argv[1], int(sys.argv[2])
seen = {}
original = households_close_figures.closed_scalars_of


def patched(view, agent_ids, tiles, baskets, columns, people, income_received, spent, floor_cost_of_person):
    seen["income"] = float(np.sum(income_received))
    seen["spent"] = float(np.sum(spent))
    seen["planned"] = float(np.sum(columns["planned_spending"]))
    seen["floor_cost"] = float(np.sum(floor_cost_of_person * people))
    return original(view, agent_ids, tiles, baskets, columns, people, income_received, spent, floor_cost_of_person)


households_close_figures.closed_scalars_of = patched
for name in dir(economy_module):
    module = getattr(economy_module, name)
    if hasattr(module, "closed_scalars_of") and module is not households_close_figures:
        setattr(module, "closed_scalars_of", patched)
import sim.economy.year_close_households as year_close_households
for name in dir(year_close_households):
    if name == "closed_scalars_of":
        setattr(year_close_households, name, patched)
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
money = setup.currency_id


def coin(agents):
    return sum(economy.record.book.balance(agent, money) for agent in agents)


print("year | cohorts' coin before -> after | received | spent | spent/received | producers' coin after | wage")
for year in range(years):
    before = coin(economy.record.cohorts)
    outcome = economy.step(inputs)
    after = coin(economy.record.cohorts)
    producers = coin(producer.agent_id for producer in economy.record.producers.values())
    print("%3d | %.4g -> %.4g | %.4g | %.4g | %.3f | %.4g | %.3f | planned %.4g floor cost %.4g" % (
        year, before, after, seen.get("income", 0.0), seen.get("spent", 0.0), seen.get("spent", 0.0) / max(seen.get("income", 1e-9), 1e-9),
        producers, outcome.wages.get(setup.unskilled_trade) or 0.0, seen.get("planned", 0.0), seen.get("floor_cost", 0.0)))
