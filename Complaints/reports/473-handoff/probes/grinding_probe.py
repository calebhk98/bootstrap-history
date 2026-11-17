"""Which grains the cohorts of one tile buy milled, year by year, and the share of their food they grind by hand (`household_work_year.grinding_plan`).
Usage: python3 grinding_probe.py <civ> <tile> <first year> <last year>"""
import random, sys
from sim.economy import api as economy_api
from sim.economy import household_work_year
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
from sim.markets.spin_up import spin_up_years

civ, tile, first, last = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
seen = []
original = household_work_year.grinding_plan


def patched(setup, record, view, cohort, hour_value):
    result = original(setup, record, view, cohort, hour_value)
    if cohort.tile == tile:
        seen.append((cohort.agent_id, tuple(result[0]), round(result[1], 4), round(hour_value, 4)))
    return result


household_work_year.grinding_plan = patched
food_rows = []
original_rows = household_work_year._food_rows


def patched_rows(setup, view, tile_id, hearth):
    result = original_rows(setup, view, tile_id, hearth)
    if tile_id == tile and hearth and result is not None:
        food_rows.append(result)
    return result


household_work_year._food_rows = patched_rows
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
print("milled as:", dict(setup.milled_as))
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
first_years, trimmed_years = spin_up_years()
count = 0
for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
    if stage == "trimmed":
        economy_api.trim_workforce_to_expected_hours(economy)
    for year in range(years):
        seen.clear()
        food_rows.clear()
        economy.step(inputs)
        if first <= count <= last:
            print(count, sorted(set(seen))[:1])
            if food_rows:
                floor, rows = food_rows[-1]
                print("    food rows (good, price, effect, share):", [(good, round(price, 3), round(effect, 3), round(share, 4)) for good, price, effect, share in rows if share > 0.005])
        count += 1
