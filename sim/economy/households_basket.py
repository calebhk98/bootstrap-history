"""What households need, as data: the needs, their floors and weights, and the goods that serve them.

The pure part lives in sim/world/need_basket.py (import its names from there); this
module adds pricing a basket at a tile from the economy's market view. Build one priced list per tile
and share it across that tile's classes.
"""
from typing import Dict, List

from sim.world import need_basket
from sim.world.need_basket import Basket, PricedNeed

from .protocols import MarketView
from .types import TileId

# basket id -> (basket, goods it names, priced needs by the tuple of those goods' prices); about one basket per tile
_priced_by_basket: Dict[int, tuple] = {}
MAX_BASKETS_KEPT = 4096
MAX_PRICINGS_KEPT = 64      # per basket: prices change every year, so old pricings are not read again


def need_prices(basket: Basket, view: MarketView, tile: TileId) -> List[PricedNeed]:
    """Each need that has a priced good on this tile (the kernel's `need_basket.need_prices` at the
    tile's market prices). Tiles seeing the same prices share one pricing of the basket."""
    kept = _priced_by_basket.get(id(basket))
    if kept is None or kept[0] is not basket:
        if len(_priced_by_basket) >= MAX_BASKETS_KEPT:
            _priced_by_basket.clear()
        goods = tuple(sorted({good for spec in basket.needs for good, _effect in spec.goods}))
        kept = _priced_by_basket[id(basket)] = (basket, goods, {})
    _basket, goods, by_prices = kept
    prices = {good: view.offered_price(good, view.area_of(good, tile)) for good in goods}
    key = tuple(prices.values())
    priced = by_prices.get(key)
    if priced is None:
        if len(by_prices) >= MAX_PRICINGS_KEPT:
            by_prices.clear()
        priced = by_prices[key] = tuple(need_basket.need_prices(basket, prices.__getitem__))
    return list(priced)
