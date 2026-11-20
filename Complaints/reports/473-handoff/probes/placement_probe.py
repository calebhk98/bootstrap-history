"""Where the opening may place a crop recipe: each tile's yield factor, whether a run pays there at the opening's prices and wages,
the lowest paying yield, and the tile's people. Usage: python3 placement_probe.py <civ> <recipe> [<recipe> ...]"""
import random, sys
from sim.economy import crop_sites, sites, location
from sim.economy.setup import recipe_tile_key
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
people = setup.opening_population_by_tile
for recipe_id in sys.argv[2:]:
    recipe = setup.recipes[recipe_id]
    every = sites.suited_tiles(recipe, setup.tiles, sorted(setup.tiles), setup.recipe_allowed)
    floor = crop_sites.lowest_paying_yield(recipe, setup.opening_prices, setup.opening_wages)
    print(recipe_id, "lowest paying yield %.3f" % floor, "suited tiles", len(every), "of", len(setup.tiles), "land per run", setup.land_per_run.get(recipe_id))
    for tile in sorted(setup.tiles):
        factor = setup.yield_factor_by_recipe_tile.get(recipe_tile_key(recipe_id, tile))
        print("   %-22s people %9.0f  yield %s  suited %s  pays %s" % (tile, people.get(tile, 0.0), "%.3f" % factor if factor is not None else "none", tile in every,
              factor is not None and crop_sites.pays(recipe, factor, setup.opening_prices, setup.opening_wages)))
