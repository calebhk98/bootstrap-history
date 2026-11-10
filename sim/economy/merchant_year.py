"""The merchants' year close over the merchant table: every merchant hears the year's prices and moves its expectations, then settles its
profit, each as one kernel call over all of them (`merchant_year_kernels`). The rules are `merchants.close_year`'s and
`merchants_news.learn_all`'s; those functions stay for a caller with one merchant."""
from typing import Sequence

import numpy

from . import merchant_year_kernels, merchants_news
from .merchant_figures import market_name
from .merchant_table import MerchantTable
from .types import Transfer

UNKNOWN = -2        # a pair not yet looked up in `PairRows`


class PairRows:
    """A number for each (good, tile) pair (a market row, a slot), a matrix indexed by two numberings (goods and tiles), filled for
    the pairs asked about. `resolve(good name, tile name)` gives the number (-1: none); with `retry_unnumbered` a -1 is asked again
    next time (a market that was not numbered may be). Reset when the `scope` (objects the answers hold for) is replaced."""

    def __init__(self, retry_unnumbered: bool) -> None:
        self.rows = numpy.full((0, 0), UNKNOWN, numpy.int64)
        self.scope: tuple = ()
        self.retry_unnumbered = retry_unnumbered

    def lookup(self, good_numbers, tile_numbers, good_names, tile_names, scope: tuple, resolve) -> numpy.ndarray:
        """The number of each (good number, tile number) pair."""
        if len(self.scope) != len(scope) or any(old is not new for old, new in zip(self.scope, scope)):
            self.rows = numpy.full((0, 0), UNKNOWN, numpy.int64)
            self.scope = scope
        if len(good_numbers) == 0:
            return numpy.zeros(0, numpy.int64)
        goods, tiles = int(good_numbers.max()) + 1, int(tile_numbers.max()) + 1
        if goods > self.rows.shape[0] or tiles > self.rows.shape[1]:
            grown = numpy.full((max(goods, self.rows.shape[0]), max(tiles, self.rows.shape[1])), UNKNOWN, numpy.int64)
            grown[:self.rows.shape[0], :self.rows.shape[1]] = self.rows
            self.rows = grown
        found = self.rows[good_numbers, tile_numbers]
        missing = numpy.flatnonzero((found == UNKNOWN) | ((found < 0) & self.retry_unnumbered))
        if len(missing):
            for pair in numpy.unique(good_numbers[missing] * self.rows.shape[1] + tile_numbers[missing]).tolist():
                good, tile = divmod(pair, self.rows.shape[1])
                self.rows[good, tile] = resolve(good_names[good], tile_names[tile])
            found = self.rows[good_numbers, tile_numbers]
        return found


BOOK_PAIRS = PairRows(retry_unnumbered=True)
TRANSIT_PAIRS = PairRows(retry_unnumbered=True)


def market_row_resolver(area_map, tables):
    """`PairRows` resolver: the goods-market row of the market area holding the tile (-1: not numbered)."""
    return lambda good, tile: tables.goods_numbers.get(market_name((good, area_map.area_of(good, tile))), -1)


def learn_rows(store: MerchantTable, rows: numpy.ndarray, news, lags: numpy.ndarray, speed: float) -> None:
    """Move the expected prices and volumes of the merchants at table `rows` toward the year's (`lags[k]`: the news lag of each price key
    for `rows[k]`); a price from a market `lag` years away is the price of that many years ago, kept in the table's price history."""
    store.flush_pending_history()
    price_rows, volume_rows = news.rows_in(store.tables)
    store.fit_columns()
    if len(news.price_keys):
        heard, kept, keys, starts, prices = merchant_year_kernels.hear_all(
            rows, price_rows, news.price_values, lags, store.history_key, store.history_starts, store.history_price)
        store.history_key, store.history_starts, store.history_price = keys, starts, prices
        cells = numpy.ix_(rows, price_rows)
        old = store.prices[cells]
        store.prices[cells] = numpy.where(kept, merchants_news.move_toward(old, heard, speed), old)
    if len(news.volume_keys):
        cells = numpy.ix_(rows, volume_rows)
        store.volumes[cells] = merchants_news.move_toward(store.volumes[cells], news.volume_values, speed)


def learn_year(store: MerchantTable, news, carriage, speed: float) -> None:
    """`learn_rows` for every merchant of the table."""
    rows = store.rank_order()
    if len(rows):
        learn_rows(store, rows, news, news.lags_for(carriage, [store.homes[row] for row in rows.tolist()]), speed)


def book_numbers(store: MerchantTable, book, rows: numpy.ndarray) -> numpy.ndarray:
    """The book's agent number of each merchant at `rows` (-1: the book has never seen it)."""
    numbers = book.agent_ids.numbers
    return numpy.array([numbers.get(store.agents[row], -1) for row in rows.tolist()], numpy.int64)


def purses(book, numbers: numpy.ndarray, currency) -> numpy.ndarray:
    """The balance of each agent number in `currency` (zero for -1)."""
    currency_number = book.currency_ids.numbers.get(currency)
    if currency_number is None:
        return numpy.zeros(len(numbers))
    cells = numpy.where(numbers >= 0, numbers, 0) * book.stride + currency_number
    return numpy.where(numbers >= 0, book.balance_table.amount[cells], 0.0)


def close_all(store: MerchantTable, book, area_map, currency, interest_rate: float, payout_share: float) -> Sequence[Transfer]:
    """Settle every merchant's year (`merchants.close_year`, after `learn_year`): the capital column moves, and the profit paid to each
    owner is returned as transfers in merchant order. A merchant's cash is its balance now, which no other merchant's close changes."""
    rows = store.rank_order()
    if len(rows) == 0:
        return ()
    store.fit_columns()
    numbers = book_numbers(store, book, rows)
    first = numpy.where(numbers >= 0, book.agent_table.first_slot[numpy.where(numbers >= 0, numbers, 0)], -1)
    table = book.stock_rows.table
    held_owner, held_good, held_tile, held_quantity = merchant_year_kernels.merchant_stock(
        first, table.next_in_agent, table.good, table.tile, table.quantity)
    resolve = market_row_resolver(area_map, store.tables)
    scope = (area_map, store.tables.goods_markets)
    held_market = BOOK_PAIRS.lookup(held_good, held_tile, book.good_ids.name_list, book.tile_ids.name_list, scope, resolve)
    position_of_row = numpy.zeros(len(store), numpy.int64)
    position_of_row[rows] = numpy.arange(len(rows))
    count = store.transit_count
    transit_market = TRANSIT_PAIRS.lookup(store.transit_good[:count], store.transit_tile[:count], store.goods.name_list,
                                          store.tiles.name_list, scope, resolve)
    owner = numpy.concatenate((held_owner, position_of_row[store.transit_owner[:count]]))
    order = numpy.argsort(owner, kind="stable")
    payout = merchant_year_kernels.settle_profits(
        rows, purses(book, numbers, currency), store.capital_base, store.prices, owner[order],
        numpy.concatenate((held_market, transit_market))[order], numpy.concatenate((held_quantity, store.transit_quantity[:count]))[order],
        float(interest_rate), payout_share)
    return [Transfer(store.agents[rows[place]], store.owners[rows[place]], currency, float(payout[place]), "merchant profit")
            for place in numpy.flatnonzero(payout > 0.0).tolist()]
