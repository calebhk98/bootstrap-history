"""Which country each tile of a setup belongs to, for every tile in one pass (`EconomySetup.country_of` for a single tile)."""
from typing import Dict


def country_by_tile(setup) -> Dict[str, str]:
    """Each of the setup's tiles to the civilisation whose people live there: the owner when the owner map names one, else the tile's own
    country, else the setup's."""
    home = setup.civ_id
    by_tile = {tile: spec.country if spec is not None and spec.country else home for tile, spec in setup.tiles.items()}
    for tile, owned in setup.tile_owners.items():
        if owned and tile in by_tile:
            by_tile[tile] = owned["owner"]
    return by_tile
