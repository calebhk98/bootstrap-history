"""What households need, as data: the needs, their floors and weights, and the goods that serve them.

The pure part lives in sim/world/need_basket.py (import its names from there); this
module adds pricing a basket at a tile from the economy's market view. Build one priced list per tile
and share it across the classes of one basket.
"""
from typing import List

from sim.world import need_basket
from sim.world.need_basket import Basket, PricedNeed

from .priced_reads import kept_need_prices, offered_prices_for
from .protocols import MarketView
from .types import TileId

TILE_BASKET_KEY = ("food", True)     # the key of the tile's own basket (a cohort with a hearth and nothing hired) in the kept reads


def need_prices(basket: Basket, view: MarketView, tile: TileId) -> List[PricedNeed]:
    """Each need that has a priced good on this tile (the kernel's `need_basket.need_prices` at the
    tile's market prices). A pass that prices many cohorts shares the result by basket (`BidMemory.priced`)."""
    goods = {good for spec in basket.needs for good, _effect in spec.goods}
    prices = offered_prices_for(view, tile, sorted(goods))
    return list(need_basket.need_prices(basket, prices.__getitem__))


def tile_need_prices(setup, view: MarketView, tile: TileId) -> List[PricedNeed]:
    """`need_prices` of the tile's own basket, kept with the view's reads until the memory is next written to
    (the list is shared, never changed)."""
    return kept_need_prices(view, lambda: setup.basket_for(tile), tile, TILE_BASKET_KEY)


def cohort_need_prices(basket: Basket, view: MarketView, tile: TileId, signature) -> List[PricedNeed]:
    """`need_prices` of a cohort's basket (`household_work_year.cohort_basket`), kept by the basket's `basket_signature`: the
    cohorts that bid and the cohorts that count what they ate share one pricing wherever they share a basket
    (the list is shared, never changed)."""
    return kept_need_prices(view, lambda: basket, tile, ("cohort_basket", signature))
