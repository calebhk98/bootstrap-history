"""Keeps the economy's cropland and tile yields on the farm model's: the held tiles' crop sites as the society's
rotation and the soil nitrogen stock now make them (`Sim.farm_sites`), not as they were when the setup was built.
"""
from sim.economy.api import recipe_tile_key, tile_costs


def follow_farm_sites(sim, held_tiles, yield_factor_by_recipe_tile, suitability=None) -> dict:
    """The setup fields that follow the farm's sites, for `Economy.change_setup`: each held tile's cropped share and
    yield factor (`tiles`), and the yield of every recipe keyed to a changed tile; empty when nothing changed."""
    tiles = dict(held_tiles)
    changed = {}
    for tile_id, site in sorted(sim.farm.sites().items()):
        tile = tiles.get(tile_id)
        if tile is None:
            continue
        followed = tile_costs.following_site(tile, site)
        if followed != tile:
            tiles[tile_id] = followed
            changed[tile_id] = followed.fertility
    if not changed:
        return {}
    return {"tiles": tiles, "yield_factor_by_recipe_tile": followed_factors(yield_factor_by_recipe_tile, changed, suitability)}


def followed_factors(yield_factor_by_recipe_tile, fertility_by_tile, suitability=None) -> dict:
    """The yield factor of every recipe-and-tile key, replaced by the tile's new fertility (times the crop's own suitability
    for the tile, where it states one) where the tile changed."""
    separator = recipe_tile_key("", "")
    suitability = suitability or {}
    return {key: (fertility_by_tile[tile_id] * suitability.get(key, 1.0) if tile_id in fertility_by_tile else factor)
            for key, factor in yield_factor_by_recipe_tile.items() for tile_id in (key.partition(separator)[2],)}
