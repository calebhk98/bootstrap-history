"""Who goes hungry in the first year: per tile, the people, the food floor, what stayed unmet, the cohorts' coin and income,
the hours on their own plots and sold, the tile's fertility and what the market made of food there.
Usage: python3 hunger_probe.py <civ> [years]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy import economy as economy_module
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ = sys.argv[1]
years = int(sys.argv[2]) if len(sys.argv) > 2 else 1
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
money = setup.currency_id
hunger = setup.hunger_need
food_goods = {good for need in setup.basket_for(setup.capital_tile).needs if need.need_id == hunger for good, _effect in need.goods}
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
for year in range(years):
    outcome = economy.step(inputs)
    rows = defaultdict(lambda: defaultdict(float))
    for key, cohort in economy.record.cohorts.items():
        row = rows[cohort.tile]
        need = next(spec for spec in setup.basket_for(cohort.tile).needs if spec.need_id == hunger)
        row["people"] += cohort.people
        row["floor"] += need.subsistence_per_person * cohort.people
        row["unmet"] += cohort.unmet_floor_by_need.get(hunger, 0.0) * (cohort.people if cohort.unmet_floor_by_need.get(hunger, 0.0) < need.subsistence_per_person * 1.5 else 1.0)
        row["raw_unmet"] += cohort.unmet_floor_by_need.get(hunger, 0.0)
        row["cash"] += economy.record.book.balance(cohort.agent_id, money)
        row["income"] += cohort.last_year_income
        row["plot"] += captured["plot"].get(cohort.agent_id, 0.0)
        row["sold"] += captured["sold"].get(cohort.agent_id, 0.0)
        row["working"] += cohort.working_people
    made = defaultdict(float)
    for (agent, good), quantity in outcome.output.items() if isinstance(next(iter(outcome.output), None), tuple) else []:
        pass
    state = economy_api.spin_up_state(economy, outcome)
    print("year", year, "unmet %.4g of food need %.4g (%.1f%%)" % (state["unmet_need"], state["food_need"], 100 * state["unmet_need"] / state["food_need"]))
    print("   %-22s %9s %7s %10s %10s %9s %9s %9s %9s %6s" % ("tile", "people", "fert", "floor", "raw unmet", "cash/hd", "income/hd", "plot h/wk", "sold h/wk", "share"))
    for tile in sorted(rows):
        row = rows[tile]
        fertility = setup.tiles[tile].fertility
        print("   %-22s %9.0f %7.3f %10.4g %10.4g %9.2f %9.2f %9.1f %9.1f %6.2f" % (tile, row["people"], fertility, row["floor"], row["raw_unmet"], row["cash"] / row["people"],
              row["income"] / row["people"], row["plot"] / max(row["working"], 1e-9), row["sold"] / max(row["working"], 1e-9), row["raw_unmet"] / row["floor"]))
