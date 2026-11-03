"""A good's one price over its market areas, and a trade's one wage over its labour areas."""
import math
from typing import Callable, Dict, List, Mapping, Optional, Set, Tuple

from .market_memory import KEY_SEPARATOR, RECENT_TRADE_YEARS


def usual_volumes(record) -> Mapping[str, float]:
    """What each market usually trades, by market key: the memory's smoothed volumes; before any is remembered, this
    year's volumes."""
    return record.memory.volume_weights or record.goods.volumes


def _markets_by_good(record, keep: Optional[Callable[[str, str], bool]]) -> Dict[str, List[Tuple[str, float, bool, float]]]:
    """Each good's priced markets in key order as (key, price, a traded price, weight): the weight is what the
    market usually trades (this year's volume before any is remembered). `keep(good, area)` drops a market."""
    weights = usual_volumes(record)
    memory = record.memory
    by_good: Dict[str, List[Tuple[str, float, bool, float]]] = {}
    for key, price in sorted(memory.prices.items()):
        good, area = key.split(KEY_SEPARATOR, 1)
        if keep is None or keep(good, area):
            by_good.setdefault(good, []).append((key, price, memory.traded_within(key, RECENT_TRADE_YEARS), weights.get(key, 0.0)))
    return by_good


def national_prices(record, keep: Optional[Callable[[str, str], bool]] = None) -> Dict[str, float]:
    """Each good's price over its market areas (those `keep` accepts, every area for None), weighted by what each
    usually trades. Only areas whose figure is a traded price count, quoted areas do not: a quote is no one's
    payment, so the price index follows trades where there are any. A good none of whose areas has a traded
    price with a weight is given the figure of its first area, which is then a quote (`MarketView.quote_kind`)."""
    prices = {}
    for good, markets in _markets_by_good(record, keep).items():
        value = math.fsum(price * weight for _key, price, traded, weight in markets if traded)
        quantity = math.fsum(weight for _key, _price, traded, weight in markets if traded)
        prices[good] = value / quantity if quantity > 0.0 else markets[0][1]
    return prices


def port_share(record, good: str, key: str) -> float:
    """The share of a good's usual traded value, over the areas `national_prices` counts, that falls to the market
    `key`: how far a move in that market moves the national price. 1.0 when no area counts."""
    markets = _markets_by_good(record, lambda each, _area: each == good).get(good, [])
    total = math.fsum(price * weight for _key, price, traded, weight in markets if traded)
    own = math.fsum(price * weight for market, price, traded, weight in markets if traded and market == key)
    return own / total if total > 0.0 else 1.0


def national_wages(record, keep: Optional[Callable[[str], bool]] = None) -> Dict[str, float]:
    """Each trade's wage per hour over its labour markets (those `keep` accepts by market key), weighted by the
    hours hired there last year; the plain mean for a trade that hired nowhere."""
    rows: Dict[str, List[Tuple[float, float]]] = {}
    for key, wage in sorted(record.memory.wages.items()):
        if keep is None or keep(key):
            rows.setdefault(key.split(KEY_SEPARATOR, 1)[0], []).append((wage, record.labour.hours_cleared_in(key)))
    wages = {}
    for trade, pairs in rows.items():
        hours = math.fsum(weight for _wage, weight in pairs)
        wages[trade] = (math.fsum(wage * weight for wage, weight in pairs) / hours if hours > 0.0
                        else math.fsum(wage for wage, _weight in pairs) / len(pairs))
    return wages


def traded_spending_weights(volumes: Mapping[str, float], prices: Mapping[str, float], goods: Set[str]) -> Dict[str, float]:
    """What each of `goods` is spent on: its volume over its areas (`volumes` by market key) at `prices`. A good
    without a price or a volume carries no weight."""
    quantity: Dict[str, float] = {}
    for key, volume in volumes.items():
        good = key.split(KEY_SEPARATOR, 1)[0]
        if good in goods and volume > 0.0:
            quantity[good] = quantity.get(good, 0.0) + volume
    return {good: amount * prices[good] for good, amount in sorted(quantity.items()) if prices.get(good, 0.0) > 0.0}
