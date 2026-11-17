"""The hours households keep at home for their own-plot plan, by need, year by year, beside the hours offered.
Usage: python3 plan_hours_probe.py <civ> [years]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, households_own
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ = sys.argv[1]
years = int(sys.argv[2]) if len(sys.argv) > 2 else 3
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
options = households_own.own_production_options(setup.recipes, setup.land_per_run, setup.basket)
print("needs a plot can grow, with the recipe it uses and the hours a need unit takes:", {need: (rows[0][1], round(rows[0][0], 4)) for need, rows in options.items()})
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
for year in range(years):
    plan_hours = defaultdict(float)
    for cohort in economy.record.cohorts.values():
        tile = setup.tiles.get(cohort.tile)
        fertility = tile.fertility if tile else 0.0
        for need, units in cohort.own_plan_by_need.items():
            rows = options.get(need)
            if rows and units > 0.0 and fertility > 0.0:
                plan_hours[need] += units * rows[0][0] / fertility
    outcome = economy.step(inputs)
    hours = sum(result.hours_offered for result in economy._last_ledger.labour_results) if hasattr(economy, "_last_ledger") else float("nan")
    print("year", year, "plan hours before the year, by need (not cut to land):", {need: "%.4g" % value for need, value in plan_hours.items()})
