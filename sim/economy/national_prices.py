"""A good's one price over its market areas, and a trade's one wage over its labour areas."""
import math
from itertools import repeat
from typing import Callable, Dict, Hashable, List, Mapping, Optional, Set, Tuple

import numpy as np

from . import price_index
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


def national_prices(record, keep: Optional[Callable[[str, str], bool]] = None, keep_token: Optional[Hashable] = None) -> Dict[str, float]:
    """Each good's price over its market areas (those `keep` accepts, every area for None), weighted by what each
    usually trades. Only areas whose figure is a traded price count, quoted areas do not: a quote is no one's
    payment, so the price index follows trades where there are any. A good none of whose areas has a traded
    price with a weight is given the figure of its first area, which is then a quote (`MarketView.price_kind`).
    `keep_token` names what `keep` accepts, so the answer is kept between calls (equal tokens, equal `keep`)."""
    memory = record.memory
    layout = price_index.layout_of(tuple(memory.prices))
    if not layout.keys:
        return {}
    keys = layout.keys
    weights = usual_volumes(record)
    snapshot = (tuple(memory.prices.values()), tuple(map(weights.get, keys, repeat(0.0))),
                tuple(map(memory.trade_age.get, keys, repeat(RECENT_TRADE_YEARS + 1))))
    if snapshot != layout.snapshot:     # the remembered figures moved since the answers were kept
        layout.snapshot, layout.answers = snapshot, {}
    answer_key = "all" if keep is None else keep_token
    if answer_key is not None and answer_key in layout.answers:
        return dict(layout.answers[answer_key])
    kept = layout.kept(keep, keep_token)
    price = np.array(snapshot[0], dtype=float)[layout.positions]
    weight = np.array(snapshot[1], dtype=float)[layout.positions]
    traded = np.array(snapshot[2], dtype=np.int64)[layout.positions] <= RECENT_TRADE_YEARS
    counted_weight = np.where(kept & traded, weight, 0.0).tolist()
    weighted = (price * np.array(counted_weight)).tolist()
    price_list = price.tolist()
    kept_list = kept.tolist()
    prices = {}
    start = 0
    for good, end in zip(layout.goods, layout.ends):
        first = next((place for place in range(start, end) if kept_list[place]), None)
        if first is not None:
            quantity = math.fsum(counted_weight[start:end])
            prices[good] = math.fsum(weighted[start:end]) / quantity if quantity > 0.0 else price_list[first]
        start = end
    if answer_key is not None:
        layout.answers[answer_key] = prices
        return dict(prices)
    return prices


def port_share(record, good: str, key: str) -> float:
    """The share of a good's usual traded value, over the areas `national_prices` counts, that falls to the market
    `key`: how far a move in that market moves the national price. 1.0 when no area counts."""
    markets = _markets_by_good(record, lambda each, _area: each == good).get(good, [])
    total = math.fsum(price * weight for _key, price, traded, weight in markets if traded)
    own = math.fsum(price * weight for market, price, traded, weight in markets if traded and market == key)
    return own / total if total > 0.0 else 1.0


def national_wages(record, keep: Optional[Callable[[str], bool]] = None, keep_token: Optional[Hashable] = None) -> Dict[str, float]:
    """Each trade's wage per hour over its labour markets (those `keep` accepts by market key), from the wages the
    labour core holds (mirrored by `labour_state.mirror_wages`, which records only a (trade, area) the core cleared: a trade
    nobody works or hires anywhere has no entry, and a reader that prices a recipe adds it by the one wage rule,
    `notional.costing_wages`; this is the figure reported as the year's wages). Weighted by the hours hired in each market last year; for a trade that hired nowhere, by the people
    working it there (the wage is what those workers would accept); with no people either, the plain mean.
    `keep_token` names what `keep` accepts, so the answer is kept between calls (equal tokens, equal `keep`)."""
    memory = record.memory
    layout = price_index.layout_of(tuple(memory.wages))
    if not layout.keys:
        return {}
    kept = layout.kept_keys(keep, keep_token).tolist()
    wage_list = np.array(list(memory.wages.values()), dtype=float)[layout.positions].tolist()
    workers = record.labour.workforce.workers
    rows: Dict[str, List[Tuple[float, float, float]]] = {}
    start = 0
    for trade, end in zip(layout.goods, layout.ends):
        for place in range(start, end):
            if kept[place]:
                people = math.fsum(workers.get(layout.areas[place], {}).get(trade, ()))
                rows.setdefault(trade, []).append((wage_list[place], record.labour.hours_cleared_in(layout.keys_grouped[place]), people))
        start = end
    wages = {}
    for trade, entries in rows.items():
        for weight_index in (1, 2):
            total = math.fsum(entry[weight_index] for entry in entries)
            if total > 0.0:
                wages[trade] = math.fsum(entry[0] * entry[weight_index] for entry in entries) / total
                break
        else:
            wages[trade] = math.fsum(entry[0] for entry in entries) / len(entries)
    return dict(sorted(wages.items()))


def traded_spending_weights(volumes: Mapping[str, float], prices: Mapping[str, float], goods: Set[str]) -> Dict[str, float]:
    """What each of `goods` is spent on: its volume over its areas (`volumes` by market key) at `prices`. A good
    without a price or a volume carries no weight."""
    quantity: Dict[str, float] = {}
    for key, volume in volumes.items():
        good = key.split(KEY_SEPARATOR, 1)[0]
        if good in goods and volume > 0.0:
            quantity[good] = quantity.get(good, 0.0) + volume
    return {good: amount * prices[good] for good, amount in sorted(quantity.items()) if prices.get(good, 0.0) > 0.0}
