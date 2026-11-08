"""A good's one price over its market areas, and a trade's one wage over its labour areas."""
import math
import weakref
from typing import Callable, Dict, Hashable, List, Mapping, Optional, Set, Tuple

import numpy as np

from sim.labour.api import grid_rows_of, hours_cleared_at, people_at, wage_means_by_group

from . import price_index
from .market_memory import KEY_SEPARATOR, RECENT_TRADE_YEARS
from .market_store import figures_for


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
    snapshot = (tuple(memory.prices.values()), tuple(figures_for(weights, keys, 0.0)),
                tuple(figures_for(memory.trade_age, keys, RECENT_TRADE_YEARS + 1)))
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
    `keep_token` names what `keep` accepts, so the mask of kept markets is kept between calls (equal tokens, equal `keep`); the
    figures are worked out on every call, since the hours hired and the workers are written by many owners."""
    memory = record.memory
    layout = price_index.layout_of(tuple(memory.wages))
    if not layout.keys:
        return {}
    kept = layout.kept_keys(keep, keep_token)
    wage = np.array(list(memory.wages.values()), dtype=float)[layout.positions]
    workforce = record.labour.workforce
    rows = grid_rows_of(workforce, *_place_names(layout))
    means, exists = wage_means_by_group(layout.ends, kept, wage, hours_cleared_at(workforce, rows), people_at(workforce, rows))
    return {trade: float(means[group]) for group, trade in sorted(enumerate(layout.goods), key=lambda each: each[1]) if exists[group]}


_place_names_of: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _place_names(layout) -> Tuple[np.ndarray, np.ndarray]:
    """(labour area, trade) of each place of the layout, as arrays, kept for the layout (the keys it was built from do not change)."""
    if layout not in _place_names_of:
        _place_names_of[layout] = (np.array(layout.areas, dtype=str), np.array(layout.good_of_place, dtype=str))
    return _place_names_of[layout]


def traded_spending_weights(volumes: Mapping[str, float], prices: Mapping[str, float], goods: Set[str]) -> Dict[str, float]:
    """What each of `goods` is spent on: its volume over its areas (`volumes` by market key) at `prices`. A good
    without a price or a volume carries no weight."""
    quantity: Dict[str, float] = {}
    for key, volume in volumes.items():
        good = key.split(KEY_SEPARATOR, 1)[0]
        if good in goods and volume > 0.0:
            quantity[good] = quantity.get(good, 0.0) + volume
    return {good: amount * prices[good] for good, amount in sorted(quantity.items()) if prices.get(good, 0.0) > 0.0}
