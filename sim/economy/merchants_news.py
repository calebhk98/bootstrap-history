"""What merchants learn from a year's clearing, as arrays shared by every merchant that closes on it.

A merchant moves its expectation of each market's price toward the price the year showed, as many years late as the
news takes to reach it (`merchants_transit.news_lag`), and its expectation of each market's volume toward the volume
traded. The year's prices and volumes are sorted into arrays once and given their rows in the market memory's goods-market
numbering (`YearNews.rows_in`); the merchants' expectations are columns of that numbering (`merchant_figures`), so
`learn_all` moves every merchant's figures for every market of the year in one array step (`move_toward`).
"""
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import merchants_transit
from .merchant_figures import market_name

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
        self._rows: Dict[int, tuple] = {}

    def lags_at(self, carriage, home_tile) -> np.ndarray:
        """For each price key, the years of news between the market and a merchant at `home_tile` (`NOT_HEARD` where the
        market's area is gone)."""
        found = self._lags.get(home_tile)
        if found is None:
            by_tile = np.array([merchants_transit.news_lag(carriage, home_tile, tile) for tile in self.tiles] + [NOT_HEARD],
                               np.int64)
            found = self._lags[home_tile] = by_tile[self.tile_of_key]      # a key with no anchor has tile -1: the last place
        return found

    def lags_for(self, carriage, home_tiles: Sequence) -> np.ndarray:
        """`lags_at` of each home tile, one row each."""
        return np.stack([self.lags_at(carriage, tile) for tile in home_tiles])

    def lags_by(self, lag_years: Callable) -> np.ndarray:
        """The lags from a function of (good, area) that gives None for a market that is gone."""
        return np.array([NOT_HEARD if lag is None else lag for lag in (lag_years(*key) for key in self.price_keys)], np.int64)


    def rows_in(self, tables) -> Tuple[np.ndarray, np.ndarray]:
        """(rows of the price keys, rows of the volume keys) in the goods-market numbering of `tables`, numbering the markets
        it has not yet numbered. Kept while the numbering stays as it is."""
        found = self._rows.get(id(tables))
        if found is not None and found[0] is tables and found[1] == tables.generation:
            return found[2], found[3]
        names = [market_name(key) for key in self.price_keys]
        same_markets = self.volume_keys == self.price_keys      # the usual year: the same markets traded and were priced
        volume_names = names if same_markets else [market_name(key) for key in self.volume_keys]
        numbers = tables.goods_numbers
        if any(name not in numbers for name in names) or any(name not in numbers for name in volume_names):
            tables.admit_goods_markets(names + volume_names)
            numbers = tables.goods_numbers
        price_rows = np.array([numbers[name] for name in names], np.int64)
        volume_rows = price_rows if same_markets else np.array([numbers[name] for name in volume_names], np.int64)
        self._rows[id(tables)] = (tables, tables.generation, price_rows, volume_rows)
        return price_rows, volume_rows


def move_toward(old: np.ndarray, values: np.ndarray, speed: float) -> np.ndarray:
    """Each figure moves a share `speed` of the way to the value, or takes it where there was none (NaN). `old` and `values`
    are arrays of any shape that broadcast."""
    return np.where(np.isnan(old), values, old + speed * (values - old))


def learn_all(merchants: Sequence, news: YearNews, lags: Sequence[np.ndarray], speed: float) -> None:
    """Move these merchants' expected prices and volumes toward the year's. `lags[i]` is the news lag of each price key for
    `merchants[i]` (`YearNews.lags_at`). Merchants of one table are moved together (`merchant_year.learn_rows`); a year's close
    moves every merchant of the record at once (`merchant_year.learn_year`)."""
    from . import merchant_year       # merchant_year imports this module's `move_toward`
    groups: Dict[int, List[int]] = {}
    for place, merchant in enumerate(merchants):
        groups.setdefault(id(merchant.expected_prices.tables), []).append(place)
    for places in groups.values():
        store, _row = merchants[places[0]]._table()
        merchant_year.learn_rows(store, np.array([merchants[place]._table()[1] for place in places], np.int64), news,
                                 np.stack([lags[place] for place in places]), speed)


def learn(merchant, news: YearNews, lags: np.ndarray, speed: float) -> None:
    """`learn_all` for one merchant."""
    learn_all([merchant], news, [lags], speed)
