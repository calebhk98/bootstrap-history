"""Whether a tile has ground left for a newcomer (the land market caps a producer's runs at the ground it is granted)."""
from typing import Iterable, Set, Tuple


def land_short_tiles(rows: Iterable[Tuple[str, float, bool]]) -> Set[str]:
    """Tiles where a producer whose recipe takes land was granted less than it asked (`land_run_cap` at or above zero):
    rows are (tile, land_run_cap, recipe takes land). All of such a tile's ground is spoken for."""
    return {tile for tile, cap, takes_land in rows if takes_land and cap >= 0.0}


def headroom_with_land(headroom_runs: float, takes_land: bool, tile_is_land_short: bool) -> float:
    """Runs a recipe can still be sited for on the tile: none for a recipe on land where the ground is all granted."""
    return 0.0 if takes_land and tile_is_land_short else headroom_runs
