"""For each market area of a staple: its people, its arable land, the land its people's food floor would take grown as that staple
at each tile's fertility, the land the opening's plots and farms hold there, and the food the opening grows there against the floor.
Usage: python3 area_land_probe.py <civ> <staple good> <staple recipe>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, titles_ground, titles_plots
from sim.engine.ui_port import Sim, load, load_civ

civ, staple, recipe_id = sys.argv[1], sys.argv[2], sys.argv[3]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
record = economy.record
area_map = setup.area_map()
hunger = setup.hunger_need
need = next(spec for spec in setup.basket_for(setup.capital_tile).needs if spec.need_id == hunger)
effect = dict(need.goods)[staple]
recipe = setup.recipes[recipe_id]
land_per_run = setup.land_per_run[recipe_id]
units_per_hectare = recipe.outputs[staple] * effect / land_per_run       # food units a hectare grows at fertility one
people, held, farm_land, grown = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
plots = titles_plots.hectares_held(setup, record)
food = dict(need.goods)
for agent_id, cohort in record.cohorts.items():
    people[cohort.tile] += cohort.people
    held[cohort.tile] += plots.get(agent_id, 0.0)
for producer in record.producers.values():
    per_run = setup.land_per_run.get(producer.recipe_id, 0.0)
    made = setup.recipes[producer.recipe_id]
    if per_run > 0.0:
        farm_land[producer.tile] += producer.expected_sales * per_run
        grown[producer.tile] += sum(producer.expected_sales * producer.yield_factor * quantity * food[good] for good, quantity in made.outputs.items() if good in food)
rows = []
for area in area_map.areas(staple):
    here = sum(people[tile] for tile in area.tiles)
    if here <= 0.0:
        continue
    arable = sum(titles_ground.arable_hectares(record, tile, setup.tiles[tile]) for tile in area.tiles)
    floor = need.subsistence_per_person * here
    could = sum(titles_ground.arable_hectares(record, tile, setup.tiles[tile]) * units_per_hectare * setup.tiles[tile].fertility for tile in area.tiles)
    rows.append((here, area.area_id, len(area.tiles), arable, could / floor, sum(farm_land[tile] for tile in area.tiles), sum(held[tile] for tile in area.tiles),
                 sum(grown[tile] for tile in area.tiles) / floor))
total = sum(row[0] for row in rows)
print("%-16s %5s %11s %6s %11s %14s %11s %11s %10s" % ("area", "tiles", "people", "share", "arable ha", "land could feed", "farms' ha", "plots' ha", "farms grow"))
short = 0.0
for here, area_id, count, arable, could, farms, plot_land, farms_grow in sorted(rows, reverse=True)[:30]:
    if could < 1.0:
        short += here
    print("%-16s %5d %11.0f %5.1f%% %11.4g %13.2fx %11.4g %11.4g %9.2fx" % (area_id, count, here, 100 * here / total, arable, could, farms, plot_land, farms_grow))
print("areas: %d; people in areas whose own arable land could not grow their food floor: %.1f%% of all" % (len(rows), 100 * short / total))
print("all: arable %.4g ha; the floor grown as the staple would take about %.4g ha" % (sum(row[3] for row in rows), sum(row[3] / row[4] for row in rows if row[4] > 0)))
