"""Keeps the economy's cropland and tile yields on the farm model's: the held tiles' crop sites as the society's
rotation and the soil nitrogen stock now make them (`Sim.farm_sites`), not as they were when the setup was built.
"""
from sim.economy.api import recipe_tile_key, tile_costs


def follow_farm_sites(sim, held_tiles, yield_factor_by_recipe_tile) -> dict:
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
    ends = {recipe_tile_key("", tile): fertility for tile, fertility in changed.items()}     # a key ends with its tile's suffix
    factors = {key: next((fertility for suffix, fertility in ends.items() if key.endswith(suffix)), factor)
               for key, factor in yield_factor_by_recipe_tile.items()}
    return {"tiles": tiles, "yield_factor_by_recipe_tile": factors}
