"""What households need, as data: the needs, their floors and weights, and the goods that serve them.

The pure part lives in sim/world/need_basket.py (import its names from there); this
module adds pricing a basket at a tile from the economy's market view. Build one priced list per tile
and share it across the classes of one basket.
"""
from typing import List

from sim.world import need_basket
from sim.world.need_basket import Basket, PricedNeed

from .protocols import MarketView
from .types import TileId


def need_prices(basket: Basket, view: MarketView, tile: TileId) -> List[PricedNeed]:
    """Each need that has a priced good on this tile (the kernel's `need_basket.need_prices` at the
    tile's market prices). A pass that prices many cohorts shares the result by basket (`BidMemory.priced`)."""
    goods = {good for spec in basket.needs for good, _effect in spec.goods}
    prices = {good: view.offered_price(good, view.area_of(good, tile)) for good in sorted(goods)}
    return list(need_basket.need_prices(basket, prices.__getitem__))
