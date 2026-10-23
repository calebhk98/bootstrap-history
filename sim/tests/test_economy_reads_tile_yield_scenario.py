"""Scenario: Complaint 537 in a game. The agent economy's land is geography's cropland and its farms yield what the tile's soil,
climate and river water give (geography's `crop_site`), the same ground the farm model and the tile food view read; once the
economy opens its farm producers carry their tile's factor. The year's yield being that factor times the weather, and the
pasture and mine producers following the weather alone, are rules in test_economy_crop_yields."""
import math

from .harness import *  # noqa: F401,F403

from sim.economy.setup import recipe_tile_key
from sim.engine import economy_port_setup
from sim.geography.api import crop_site
from sim.world import land

game = unopened_sim()
setup = economy_port_setup.build_setup(game)
share = 1.0 - game.labour.farming_technique().rotation.fallow_share_of_holding
held = economy_port_setup.civilisation_tiles(game.civ, game.world_map)[0]

cropland = {tile_id: setup.tiles[tile_id].land_area_km2 * 100.0 * setup.tiles[tile_id].cropped_fraction for tile_id in held}
tillage = game.labour.farming_technique().toolkit.tillage_capacity
sites = {tile_id: crop_site(tile_id, share, game.world_map, tillage_capacity=tillage) for tile_id in held}
check("each tile's cropland is geography's cropped hectares",
      all(math.isclose(cropland[tile_id], (sites[tile_id].cropped_hectares if sites[tile_id].yield_factor > 0.0 else 0.0), rel_tol=1e-9, abs_tol=1e-9) for tile_id in held))
check("the economy's cropland equals the farm model's ceiling",
      math.isclose(sum(cropland.values()), land.territory_cropland(game.farm_sites()).cropped_hectares, rel_tol=1e-9))
check("each tile's yield factor is geography's",
      all(math.isclose(setup.tiles[tile_id].fertility, sites[tile_id].yield_factor, rel_tol=1e-9, abs_tol=1e-9)
          for tile_id in held))

keyed = {key.partition("@")[0] for key in setup.yield_factor_by_recipe_tile}
farm_recipes = sorted(keyed)
check("crop recipes read the tile yield", bool(farm_recipes), farm_recipes)
check("pasture, forest and mine recipes do not", bool(set(setup.land_per_run) - keyed) and keyed <= set(setup.land_per_run))
watered = [tile_id for tile_id in held if sites[tile_id].yield_factor > 0.0]
best, worst = max(watered, key=lambda tile_id: sites[tile_id].yield_factor), min(watered, key=lambda tile_id: sites[tile_id].yield_factor)
check("the held tiles differ in yield", sites[best].yield_factor > sites[worst].yield_factor * 1.05,
      (sites[best].yield_factor, sites[worst].yield_factor))
for recipe_id in farm_recipes[:1]:
    check("a farm run yields more on the better tile (the opening's per-recipe site yield)",
          setup.yield_factor_by_recipe_tile[recipe_tile_key(recipe_id, best)]
          > setup.yield_factor_by_recipe_tile[recipe_tile_key(recipe_id, worst)])
    check("the site yield is the tile's yield factor",
          math.isclose(setup.yield_factor_by_recipe_tile[recipe_tile_key(recipe_id, best)], sites[best].yield_factor))

# The opened economy: farm producers carry their tile's yield factor (after the hidden years), so the same run
# gives more on the better tile.
opened = sim()
agent = opened.economy.agent
economy = agent.economy()
farms = {producer.tile: producer for producer in economy.record.producers.values() if producer.recipe_id == farm_recipes[0]}
ranked = sorted((tile_id for tile_id in farms if sites.get(tile_id) is not None and sites[tile_id].yield_factor > 0.0),
                key=lambda tile_id: sites[tile_id].yield_factor)
check("farm producers stand on tiles of different yield", len(ranked) >= 2, ranked)
if len(ranked) >= 2:
    check("a farm producer on the better-yielding tile yields more per run",
          farms[ranked[-1]].yield_factor > farms[ranked[0]].yield_factor,
          (farms[ranked[-1]].yield_factor, farms[ranked[0]].yield_factor))
    check("a farm run's yield is its tile's factor",
          all(math.isclose(farms[tile_id].yield_factor, sites[tile_id].yield_factor, rel_tol=1e-9) for tile_id in ranked))
