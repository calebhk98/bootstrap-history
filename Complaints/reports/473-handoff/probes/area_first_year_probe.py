"""The first year by market area of a staple: people, food unmet, plot hours, and the area's makers of the staple (runs sized, staffed,
worked, land cap as shares of the runs sized) with what the farms hold of their tools. Usage: python3 area_first_year_probe.py <civ> <staple good>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, economy as economy_module
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages

civ, staple = sys.argv[1], sys.argv[2]
captured = {}
original = economy_module.Economy._outcome
def patched(self, ledger, level, extraction, stocks_at_start):
    captured["plot"] = {agent: sum(hours.values()) for agent, hours in ledger.own_plot_hours.items()}
    return original(self, ledger, level, extraction, stocks_at_start)
economy_module.Economy._outcome = patched
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
record = economy.record
area_map = setup.area_map()
hunger = setup.hunger_need
need = next(spec for spec in setup.basket_for(setup.capital_tile).needs if spec.need_id == hunger)
sized = {producer_id: producer.expected_sales for producer_id, producer in record.producers.items()}
outcome = economy.step(spin_up_stages.year_inputs(economy))
people, plot, working = defaultdict(float), defaultdict(float), defaultdict(float)
for cohort in record.cohorts.values():
    people[cohort.tile] += cohort.people
    plot[cohort.tile] += captured["plot"].get(cohort.agent_id, 0.0)
    working[cohort.tile] += cohort.working_people
rows = defaultdict(lambda: defaultdict(float))
for producer_id, producer in record.producers.items():
    recipe = setup.recipes[producer.recipe_id]
    if staple not in recipe.outputs:
        continue
    row = rows[producer.tile]
    row["sized"] += sized.get(producer_id, 0.0)
    row["staffed"] += producer.staffed_runs or 0.0
    row["worked"] += max(producer.last_runs, 0.0)
    row["cap"] += producer.land_run_cap if producer.land_run_cap is not None else sized.get(producer_id, 0.0)
print("%-14s %5s %11s %7s %9s | staple runs: %10s %8s %8s %8s" % ("area", "tiles", "people", "unmet", "plot h/wk", "sized", "staffed", "worked", "land cap"))
for area in sorted(area_map.areas(staple), key=lambda area: -sum(people[tile] for tile in area.tiles))[:14]:
    here = sum(people[tile] for tile in area.tiles)
    if here <= 0.0:
        continue
    unmet = sum(outcome.hunger_by_tile.get(tile, 0.0) for tile in area.tiles) / (need.subsistence_per_person * here)
    total = defaultdict(float)
    for tile in area.tiles:
        for name, value in rows[tile].items():
            total[name] += value
    base = total["sized"] or 1.0
    print("%-14s %5d %11.0f %6.0f%% %9.1f | %22.4g %8.2f %8.2f %8.2f" % (area.area_id, len(area.tiles), here, 100 * unmet,
          sum(plot[tile] for tile in area.tiles) / max(sum(working[tile] for tile in area.tiles), 1e-9), total["sized"], total["staffed"] / base, total["worked"] / base, total["cap"] / base))
