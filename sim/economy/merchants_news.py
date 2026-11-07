"""What merchants learn from a year's clearing, as arrays shared by every merchant that closes on it.

A merchant moves its expectation of each market's price toward the price the year showed, as many years late as the
news takes to reach it (`merchants_transit.news_lag`), and its expectation of each market's volume toward the volume
traded. The year's prices and volumes are sorted into arrays once; each merchant adds its lags and updates its
expectations in one pass, leaving the record's dictionaries as they were.
"""
from itertools import compress
from typing import Callable, Mapping, Optional, Sequence

import numpy as np

from . import merchants_transit

NOT_HEARD = -(10 ** 9)      # the lag of a market whose area is gone from the map: no news comes from it


class YearNews:
    """The year's learned (good, area) prices and volumes, sorted by key, with the anchor tile of each priced market."""

    def __init__(self, prices: Mapping, volumes: Mapping, anchors: Optional[Mapping] = None):
        self.price_keys = sorted(prices)
        self.price_values = np.array([prices[key] for key in self.price_keys], np.float64)
        self.volume_keys = sorted(volumes)
        self.volume_values = np.array([volumes[key] for key in self.volume_keys], np.float64)
        self.anchors = anchors
        if anchors is not None:
            tiles = sorted({anchors[key] for key in self.price_keys if key in anchors})
            position = {tile: place for place, tile in enumerate(tiles)}
            self.tiles = tiles
            self.tile_of_key = np.array([position.get(anchors.get(key), -1) for key in self.price_keys], np.int64)
        self._lags = {}

    def lags_at(self, carriage, home_tile) -> np.ndarray:
        """For each price key, the years of news between the market and a merchant at `home_tile` (`NOT_HEARD` where the
        market's area is gone)."""
        found = self._lags.get(home_tile)
        if found is None:
            by_tile = np.array([merchants_transit.news_lag(carriage, home_tile, tile) for tile in self.tiles] + [NOT_HEARD],
                               np.int64)
            found = self._lags[home_tile] = by_tile[self.tile_of_key]      # a key with no anchor has tile -1: the last place
        return found

    def lags_by(self, lag_years: Callable) -> np.ndarray:
        """The lags from a function of (good, area) that gives None for a market that is gone."""
        return np.array([NOT_HEARD if lag is None else lag for lag in (lag_years(*key) for key in self.price_keys)], np.int64)


def learn(merchant, news: YearNews, lags: np.ndarray, speed: float) -> None:
    """Move the merchant's expected prices and volumes toward the year's, a price from a market `lag` years of news away
    that many years late (`merchants_transit.heard`)."""
    prices = news.price_values
    keys = news.price_keys
    heard = prices.copy()
    kept = lags > NOT_HEARD
    late = np.flatnonzero(lags > 0)
    for place in late.tolist():       # a price that has to travel is the price of years ago, or none yet
        price = merchants_transit.heard(merchant, keys[place], float(prices[place]), int(lags[place]))
        if price is None:
            kept[place] = False
        else:
            heard[place] = price
    _move(merchant.expected_prices, keys, heard, kept, speed)
    _move(merchant.expected_volumes, news.volume_keys, news.volume_values, None, speed)


def _move(expected: dict, keys: Sequence, values: np.ndarray, kept: Optional[np.ndarray], speed: float) -> None:
    """expected[key] moves a share `speed` of the way to the value, or takes it when there was none."""
    if not len(keys):
        return
    old = np.array(list(map(expected.get, keys)), np.float64)      # a None becomes NaN
    moved = np.where(np.isnan(old), values, old + speed * (values - old))
    if kept is None:
        expected.update(zip(keys, moved.tolist()))
    else:
        expected.update(zip(compress(keys, kept.tolist()), moved[kept].tolist()))
