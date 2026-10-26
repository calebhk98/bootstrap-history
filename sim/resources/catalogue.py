"""What the map's catalogue says about workings: which materials are priced from their deposits' works, and what a mine
of one supplies. Both are kept per map."""
import functools

from sim.geography.api import mine_demand_goods, works_priced_from_deposits

from . import rules


@functools.lru_cache(maxsize=None)
def works_priced_materials(world_map):
    """Materials whose mine running cost comes from the deposits' physical works, from the map's catalogue."""
    return works_priced_from_deposits(world_map)


@functools.lru_cache(maxsize=None)
def demand_goods_by_material(world_map):
    return mine_demand_goods(world_map)


def base_mine_catalog_hint():
    """The catalogue hint on the base map, for help text written before any game exists."""
    return rules.catalog_hint(works_priced_materials(None))
