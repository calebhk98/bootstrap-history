"""Which materials the base map's catalogue prices from their deposits' works, kept per map."""
import functools

from sim.geography.api import works_priced_from_deposits

from . import rules


@functools.lru_cache(maxsize=None)
def works_priced_materials(world_map):
    """Materials whose mine running cost comes from the deposits' physical works, from the map's catalogue."""
    return works_priced_from_deposits(world_map)


def base_mine_catalog_hint():
    """The catalogue hint on the base map, for help text written before any game exists."""
    return rules.catalog_hint(works_priced_materials(None))
