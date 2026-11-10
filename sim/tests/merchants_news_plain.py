"""What a merchant learned from a year as it was written over the merchant's two dictionaries, kept as the reference the
column step (`merchants_news.learn_all`) is tested against (`test_year_speed_merchants_news`). Do not use it in the game."""
from itertools import compress
from typing import Optional, Sequence

import numpy as np

from sim.economy import merchants_transit
from sim.economy.merchants_news import NOT_HEARD, YearNews


def learn(merchant, news: YearNews, lags: np.ndarray, speed: float) -> None:
    """`merchants_news.learn` when `merchant.expected_prices` and `expected_volumes` were dicts."""
    prices = news.price_values
    keys = news.price_keys
    heard = prices.copy()
    kept = lags > NOT_HEARD
    for place in np.flatnonzero(lags > 0).tolist():
        price = merchants_transit.heard(merchant, keys[place], float(prices[place]), int(lags[place]))
        if price is None:
            kept[place] = False
        else:
            heard[place] = price
    move(merchant.expected_prices, keys, heard, kept, speed)
    move(merchant.expected_volumes, news.volume_keys, news.volume_values, None, speed)


def move(expected: dict, keys: Sequence, values: np.ndarray, kept: Optional[np.ndarray], speed: float) -> None:
    if not len(keys):
        return
    old = np.array(list(map(expected.get, keys)), np.float64)
    moved = np.where(np.isnan(old), values, old + speed * (values - old))
    if kept is None:
        expected.update(zip(keys, moved.tolist()))
    else:
        expected.update(zip(compress(keys, kept.tolist()), moved[kept].tolist()))
