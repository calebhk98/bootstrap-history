"""Each opening pass of a solve, for one tile: the plot land its demand assumed, the land its producers asked for and were granted,
the tile's cropland, and the land the households hold after the pass's land market. Usage: python3 plot_pass_probe.py <civ> <tile>"""
import random, sys
from sim.economy import api as economy_api, land_market, opening_rent, titles_ground, titles_plots
from sim.engine.ui_port import Sim, load, load_civ

civ, tile = sys.argv[1], sys.argv[2]
original = opening_rent.settle
count = [0]
def settle(setup, record, view, plot_hectares, plot_returns, *rest, **more):
    answer = original(setup, record, view, plot_hectares, plot_returns, *rest, **more)
    held = titles_plots.hectares_held(setup, record)
    here = sum(held.get(agent_id, 0.0) for agent_id, cohort in record.cohorts.items() if cohort.tile == tile)
    asked = sum(producer.expected_sales * setup.land_per_run.get(producer.recipe_id, 0.0) for producer in record.producers.values() if producer.tile == tile)
    capped = sum((producer.land_run_cap if producer.land_run_cap is not None else producer.expected_sales) * setup.land_per_run.get(producer.recipe_id, 0.0)
                 for producer in record.producers.values() if producer.tile == tile)
    count[0] += 1
    print("pass %d: plots assumed %.4g ha, producers asked %.4g granted %.4g, cropland %.4g, ceded %.4g, plot value %.4g, held after %.4g" % (
        count[0], plot_hectares.get(tile, 0.0), asked, capped, titles_ground.arable_hectares(record, tile, setup.tiles[tile]),
        record.land.land_ceded.get(tile, 0.0), plot_returns.get(tile, float("nan")), here), flush=True)
    return answer
opening_rent.settle = settle
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
