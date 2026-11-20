"""For chosen tiles: each land-taking recipe that makes a food, its yield factor on the tile, whether the opening may place it there
(a run pays at the opening's prices) and the food units a hectare gives. Usage: python3 crop_suit_probe.py <civ> <tile> [<tile> ...]"""
import random, sys
from sim.economy import location
from sim.economy.setup import recipe_tile_key
from sim.engine.ui_port import Sim, load, load_civ
civ, tiles = sys.argv[1], sys.argv[2:]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
hunger = setup.hunger_need
need = next(spec for spec in setup.basket_for(setup.capital_tile).needs if spec.need_id == hunger)
food = dict(need.goods)
for tile in tiles:
    spec = setup.tiles[tile]
    print(tile, "fertility %.3f climate %s cropland %.4g ha" % (spec.fertility, spec.climate_class, spec.cropland_hectares))
    basket = setup.basket_for(tile)
    local = next(each for each in basket.needs if each.need_id == hunger)
    print("   food goods of the tile's basket:", [good for good, _effect in local.goods][:14])
    for recipe_id, recipe in sorted(setup.recipes.items()):
        land = setup.land_per_run.get(recipe_id, 0.0)
        made = sum(quantity * food[good] for good, quantity in recipe.outputs.items() if good in food)
        if land <= 0.0 or made <= 0.0:
            continue
        factor = setup.yield_factor_by_recipe_tile.get(recipe_tile_key(recipe_id, tile), 1.0)
        placed = tile in location._placed_tiles(setup, recipe)
        print("   %-22s yield factor %.3f allowed %s placed %s  food units a hectare %.0f  price %s" % (recipe_id, factor, setup.recipe_allowed(recipe_id, tile), placed,
              made / land * factor, {good: round(setup.opening_prices.get(good, float("nan")), 3) for good in recipe.outputs if good in food}))
