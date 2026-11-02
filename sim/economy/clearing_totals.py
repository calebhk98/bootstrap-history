"""A market's year across every clearing it had: the first round and the respend rounds that follow it."""
import math
from typing import Dict, Iterable, Tuple

from .types import AreaId, ClearingResult, GoodId

MarketKey = Tuple[GoodId, AreaId]


def market_totals(clearings: Iterable[ClearingResult]) -> Tuple[Dict[MarketKey, float], Dict[MarketKey, float]]:
    """(quantity, price) by (good, area): the quantity summed over the market's clearings and the price weighted by
    quantity. A market that traded nothing keeps the last price it was quoted at, which is not a price traded at."""
    rounds: Dict[MarketKey, list] = {}
    for result in clearings:
        rounds.setdefault((result.good, result.area), []).append(result)
    quantity = {key: math.fsum(result.quantity for result in results) for key, results in rounds.items()}
    price = {key: (math.fsum(result.quantity * result.price for result in results) / quantity[key]
                   if quantity[key] > 0.0 else results[-1].price)
             for key, results in rounds.items()}
    return quantity, price
