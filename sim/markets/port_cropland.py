"""Keeps the economy's cropland and tile yields on the farm model's: the held tiles' crop sites as the society's
rotation and the soil nitrogen stock now make them (`Sim.farm_sites`), not as they were when the setup was built.
"""
from sim.economy.api import tile_costs


def follow_farm_sites(sim, setup) -> None:
    """Set each held tile's cropped share and yield factor, and the yield of every crop recipe on it, from the farm's sites."""
    changed = {}
    for tile_id, site in sorted(sim.farm_sites().items()):
        tile = setup.tiles.get(tile_id)
        if tile is None:
            continue
        followed = tile_costs.following_site(tile, site)
        if followed != tile:
            setup.tiles[tile_id] = followed
            changed[tile_id] = followed.fertility
    if changed:
        for key in setup.yield_factor_by_recipe_tile:
            tile_id = key.rpartition("@")[2]
            if tile_id in changed:
                setup.yield_factor_by_recipe_tile[key] = changed[tile_id]
