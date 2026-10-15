"""What a good costs on one tile, and how far a larger order moves it.

A tile belongs to one market area for each good. The price a buyer there pays is the price its area's market
cleared at, over the price the country's areas show together, carried onto the price the game is shown (which
estimates a good that has not traded lately from what it costs to make). A tile whose area has not cleared lately
pays the shown price. The book the area last cleared is summarised (`market_curves`), so the answer to "what if I
buy this much more" is the same clearing with one more order.
"""
import math
from typing import Dict, Optional, Set, Tuple

from . import country_figures, market_curves
from .market_memory import market_key
from .notional import RECENT_TRADE_YEARS, shown_prices


def _area_on(economy, good: str, tile: str) -> Optional[str]:
    """The market area of a good that holds the tile; None when the economy has no market for the good or the
    tile is not in it."""
    try:
        return economy.area_map.area_of(good, tile)
    except KeyError:
        return None


def prices_at(economy, tile: str) -> Tuple[Dict[str, float], Set[str]]:
    """(price of each good on the tile, goods whose shown price is not a market's) in the economy's unit. The
    country of the tile is the one whose areas weigh the national price."""
    setup, memory = economy.setup, economy.record.memory
    nationwide = country_figures.prices(economy, setup.country_of(tile))
    shown, stale = shown_prices(setup, economy.record, nationwide)
    prices = {}
    for good, price in shown.items():
        area = None if good in stale else _area_on(economy, good, tile)
        key = None if area is None else market_key(good, area)
        local = memory.prices.get(key) if key is not None and memory.trade_age.get(key, math.inf) <= RECENT_TRADE_YEARS else None
        national = nationwide.get(good)
        prices[good] = price * local / national if local and national and local > 0.0 and national > 0.0 else price
    return prices, stale


def offered_units(economy, good: str, tile: str) -> Optional[float]:
    """Units the sellers in the tile's market area for the good held at its last clearing; None when the area
    has no book for it."""
    area = _area_on(economy, good, tile)
    curve = None if area is None else economy.record.curves.get(market_key(good, area))
    if curve is None:
        return None
    return math.fsum(quantity for _price, quantity in curve["offers"])


def price_response_at(economy, good: str, tile: str, landed_units: float, taken_units: float) -> Optional[float]:
    """Factor on the price in the tile's market area once `landed_units` more are offered in it and
    `taken_units` more are bought; None when the area's book traded nothing, infinite when more is taken than
    the sellers hold."""
    area = _area_on(economy, good, tile)
    curve = None if area is None else economy.record.curves.get(market_key(good, area))
    if curve is None:
        return None
    return market_curves.price_response(curve, good, economy.record.memory.prices.get(market_key(good, area)),
                                        landed_units, taken_units)
