"""What the tiles a society holds give in food and game, as functions of the holding and the stock they are given.

The wild stock is plain data the game saves ({tile: {species: share left}}, food_wild_stock.py). The wild stock,
the farming technique and the soil nitrogen factors come in as arguments, so this module reads nothing from the
simulation; the labour bound on hunting stays with the caller (sim/engine/food_supply.py).
"""
from sim.geography.queries import crop_site, draw_wild_stock, food_potential, hunted_kcal
from sim.geography.tile_holdings import tiles_held


def crop_sites(civ, world_map, cropped_share, nutrient_factors, tillage_capacity=1.0):
    """{tile: crop site} over the held tiles under a rotation that crops `cropped_share`; `nutrient_factors` is the
    soil nitrogen yield factor by tile (a tile with none is native);
    `tillage_capacity` is the share of heavy ground the toolkit opens."""
    return {tile_id: crop_site(tile_id, cropped_share, world_map, nutrient_factors.get(tile_id, 1.0), tillage_capacity)
            for tile_id in tiles_held(civ, world_map)}


def food_kcal_by_source(civ, world_map, wild_stock, crop_technique, nutrient_factors):
    """{source id: kcal a year} summed over the held tiles, game thinned by the wild stock, before any labour bound."""
    totals = {}
    for tile_id in tiles_held(civ, world_map):
        for source_id, kcal in food_potential(
                tile_id, None, world_map, wild_stock, crop_technique, nutrient_factors)["kcal_per_year"].items():
            totals[source_id] = totals.get(source_id, 0.0) + kcal
    return totals


def huntable_kcal(civ, world_map, wild_stock):
    """{tile: {species: kcal} the held tile's game could give this year}."""
    return {tile_id: hunted_kcal(tile_id, wild_stock, world_map) for tile_id in tiles_held(civ, world_map)}


def take_hunt(wild_stock, available, share, world_map):
    """The wild stock after hunters take `share` of `available` (from `huntable_kcal`) on every tile."""
    for tile_id, by_species in available.items():
        wild_stock = draw_wild_stock(
            wild_stock, tile_id, {species: kcal * share for species, kcal in by_species.items()}, world_map)
    return wild_stock
