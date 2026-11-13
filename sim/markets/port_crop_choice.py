"""Which crop a tile suits: each crop recipe may state the climate it grows in (`grows_where`: temperature and water
envelopes), and geography says how that crop's yield on a tile compares with the reference field's there. The
economy's entry rules then place each crop where a run pays at the tile's prices, so the tile's crop is the one that
pays best there."""
from sim.geography.api import crop_suitability, tile_ids

GROWS_WHERE = "grows_where"


def crop_suitabilities(production, recipes, tiles, world_map, recipe_tile_key) -> dict:
    """{recipe@tile: the crop's yield against the reference field's on the tile} for the recipes that state `grows_where`,
    on the tiles the map knows; a recipe or tile without one is not listed (it counts as one)."""
    known = set(tile_ids(world_map))
    result = {}
    for recipe_id in sorted(recipes):
        where = production[recipe_id].get(GROWS_WHERE)
        if not where:
            continue
        for tile_id in sorted(tiles):
            if tile_id in known:
                result[recipe_tile_key(recipe_id, tile_id)] = crop_suitability(tile_id, where["temperature"], where["water"], world_map)
    return result
