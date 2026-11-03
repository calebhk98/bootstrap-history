"""A market's year across every clearing it had: the first round and the respend rounds that follow it."""
import math
from typing import Dict, Iterable, Mapping, Optional, Tuple

from .types import AreaId, ClearingResult, GoodId

MarketKey = Tuple[GoodId, AreaId]


def market_totals(clearings: Iterable[ClearingResult], delivered: Mapping[MarketKey, float]
                  ) -> Tuple[Dict[MarketKey, float], Dict[MarketKey, Optional[float]]]:
    """(quantity, price) by (good, area). The quantity is what was delivered in the market over its clearings: that is
    what traded, and settlement can deliver less than a clearing matched when a buyer cannot pay. The price is the
    clearing prices weighted by the quantity each cleared, since delivery is not kept per clearing and a short payment
    changes who got the goods, not the price they were matched at. A market with nothing delivered keeps the last price
    it was quoted at (None when it had none), which is not a price traded at."""
    rounds: Dict[MarketKey, list] = {}
    for result in clearings:
        rounds.setdefault((result.good, result.area), []).append(result)
    quantity = {key: delivered.get(key, 0.0) for key in rounds}
    price: Dict[MarketKey, Optional[float]] = {}
    for key, results in rounds.items():
        cleared = math.fsum(result.quantity for result in results)
        if quantity[key] > 0.0 and cleared > 0.0:
            price[key] = math.fsum(result.quantity * result.price for result in results if result.quantity > 0.0) / cleared
        else:
            price[key] = results[-1].price
    return quantity, price
