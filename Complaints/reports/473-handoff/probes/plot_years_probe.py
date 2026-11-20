"""One tile by year over a member's spin-up: hours on its households' plots a worker, hours they sold, land ceded to producers, the plot
land held, the producers' cropland asked and capped, the tile's posted rent, and all hired hours. Usage: python3 plot_years_probe.py <civ> <member> <tile> [years]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, economy as economy_module, land_market, titles_plots
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages
from sim.markets.spin_up_ensemble import cash_factor
from sim.markets.spin_up_run import spin_up_years

civ, member, tile = sys.argv[1], int(sys.argv[2]), sys.argv[3]
captured = {}
original = economy_module.Economy._outcome
def patched(self, ledger, level, extraction, stocks_at_start):
    captured["plot"] = {agent: sum(hours.values()) for agent, hours in ledger.own_plot_hours.items()}
    captured["sold"] = dict(ledger.hours_sold)
    return original(self, ledger, level, extraction, stocks_at_start)
economy_module.Economy._outcome = patched
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
if cash_factor(member) != 1.0:
    spin_up_stages.perturb_household_cash(economy, cash_factor(member))
inputs = spin_up_stages.year_inputs(economy)
record = economy.record
first, trimmed = spin_up_years()
years = int(sys.argv[4]) if len(sys.argv) > 4 else first + trimmed
cropland = land_market.cropland_recipes(setup.land_per_run, setup.site_limits)
print("year  hired(all)  plot h/wk  sold h/wk  ceded ha  plots held ha  producers ask ha  capped ha  rent/ha")
base = None
for year in range(years):
    if year == first:
        economy_api.trim_workforce_to_expected_hours(economy)
    outcome = economy.step(inputs)
    base = base or outcome.hired_hours
    working = sum(cohort.working_people for cohort in record.cohorts.values() if cohort.tile == tile)
    plot = sum(captured["plot"].get(cohort.agent_id, 0.0) for cohort in record.cohorts.values() if cohort.tile == tile)
    sold = sum(captured["sold"].get(cohort.agent_id, 0.0) for cohort in record.cohorts.values() if cohort.tile == tile)
    held = titles_plots.hectares_held(setup, record)
    here = sum(held.get(cohort.agent_id, 0.0) for cohort in record.cohorts.values() if cohort.tile == tile)
    asked = sum(producer.expected_sales * setup.land_per_run[producer.recipe_id] for producer in record.producers.values()
                if producer.tile == tile and producer.recipe_id in cropland)
    capped = sum(producer.land_run_cap * setup.land_per_run[producer.recipe_id] for producer in record.producers.values()
                 if producer.tile == tile and producer.recipe_id in cropland and producer.land_run_cap is not None)
    print("%4d  %9.3f  %9.1f  %9.1f  %9.4g  %12.4g  %15.4g  %9.4g  %7.3f" % (year, outcome.hired_hours / base, plot / working, sold / working,
          record.land.land_ceded.get(tile, 0.0), here, asked, capped, record.land.land_rent.get(tile, 0.0)))
