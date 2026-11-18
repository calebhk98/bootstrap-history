"""The land the opening's demand assumed each tile's households work as plots, against the land they hold once the opening's land
market has settled, and the share of the tile's food floor the assumed plots grow. Usage: python3 plot_land_probe.py <civ>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, opening_rent, titles_plots
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
seen = {}
original = opening_rent.settle
def settle(setup, record, view, plot_hectares, plot_returns, *rest, **more):
    seen["assumed"] = dict(plot_hectares)
    return original(setup, record, view, plot_hectares, plot_returns, *rest, **more)
opening_rent.settle = settle
import os
if os.environ.get("ABLATE"):       # experiment switches (ablations.py beside this file)
    import ablations
    ablations.apply(os.environ["ABLATE"])
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
record = economy.record
held = titles_plots.hectares_held(setup, record)
by_tile, people = defaultdict(float), defaultdict(float)
for agent_id, cohort in record.cohorts.items():
    by_tile[cohort.tile] += held.get(agent_id, 0.0)
    people[cohort.tile] += cohort.people
farm = defaultdict(float)
for producer in record.producers.values():
    per_run = setup.land_per_run.get(producer.recipe_id, 0.0)
    if per_run > 0.0:
        farm[producer.tile] += producer.capacity_runs * per_run
print("%-12s %10s %6s %14s %14s %14s %12s" % ("tile", "people", "fert", "plots assumed", "plots held", "farms' land", "tile arable"))
total_assumed = total_held = 0.0
for tile in sorted(people, key=lambda tile: -people[tile])[:26]:
    spec = setup.tiles[tile]
    assumed = seen["assumed"].get(tile, 0.0)
    total_assumed += assumed; total_held += by_tile[tile]
    print("%-12s %10.0f %6.3f %14.4g %14.4g %14.4g %12s" % (tile, people[tile], spec.fertility, assumed, by_tile[tile], farm[tile],
          getattr(spec, "arable_hectares", getattr(spec, "farmland_hectares", "?"))))
print("all tiles: plots assumed %.4g hectares, held after the land market %.4g" % (sum(seen["assumed"].values()), sum(by_tile.values())))
