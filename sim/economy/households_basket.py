"""What households need, as data: the needs, their floors and weights, and the goods that serve them.

The pure part lives in sim/world/need_basket.py (re-exported here so callers keep one import); this
module adds pricing a basket at a tile from the economy's market view. Build one priced list per tile
and share it across that tile's classes.
"""
from typing import List

from sim.world import need_basket
from sim.world.need_basket import (Basket, NeedSpec, PricedNeed, make_basket, need_units, price_ceilings,
                                   satiation_limit, subsistence_cost_per_person)

from .protocols import MarketView
from .types import TileId

__all__ = ["Basket", "NeedSpec", "PricedNeed", "make_basket", "need_prices", "need_units", "price_ceilings",
           "satiation_limit", "subsistence_cost_per_person"]


def need_prices(basket: Basket, view: MarketView, tile: TileId) -> List[PricedNeed]:
    """Each need that has a priced good on this tile (the kernel's `need_basket.need_prices` at the
    tile's market prices)."""
    return need_basket.need_prices(basket, lambda good: view.price(good, view.area_of(good, tile)))
