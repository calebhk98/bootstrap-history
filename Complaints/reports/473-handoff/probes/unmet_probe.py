"""What floors households go short of in the first years, by need, and the own-plot plan they carry into the next year.
Usage: python3 unmet_probe.py <civ> [years]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ = sys.argv[1]
years = int(sys.argv[2]) if len(sys.argv) > 2 else 2
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
for year in range(years):
    economy.step(inputs)
    unmet, plan, floor = defaultdict(float), defaultdict(float), defaultdict(float)
    short_cohorts = 0
    for cohort in economy.record.cohorts.values():
        for need in setup.basket_for(cohort.tile).needs:
            floor[need.need_id] += need.subsistence_per_person * cohort.people
        for need, units in cohort.unmet_floor_by_need.items():
            unmet[need] += units
        for need, units in cohort.own_plan_by_need.items():
            plan[need] += units
        short_cohorts += any(units > 0.0 for units in cohort.unmet_floor_by_need.values())
    print("year", year, "cohorts short of a floor: %d of %d" % (short_cohorts, len(economy.record.cohorts)))
    for need in sorted(floor):
        if floor[need] > 0.0 or unmet[need] > 0.0 or plan[need] > 0.0:
            print("   %-20s floor %10.4g  unmet %10.4g (%5.1f%%)  plan carried %10.4g (%5.1f%% of the floor)" % (
                need, floor[need], unmet[need], 100 * unmet[need] / floor[need] if floor[need] else 0.0, plan[need], 100 * plan[need] / floor[need] if floor[need] else 0.0))
