"""The year's figures of every goods market that cleared, as one table (`GoodsYearMarkets`), in the order the markets cleared.

A row holds what the respend rounds and the year's notes read and change market by market: the units delivered and wanted over all
rounds, what the last round left on offer, the years the market lacked bids or offers, and the price the memory held when the year
began. `goods_respend_year.LeftMarket` is a view of one row plus the objects a market on the objects still needs; the respend's answer
is scattered into the columns (`add_rounds`) and the year's records (`_record_year_markets`) and the memory's notes read them whole
(`rows_in_order`). Every column is a number: a missing price is NaN (never zero)."""
from typing import Sequence

import numpy

from sim.compiled_tables.growth import reserve_rows
from sim.compiled_tables.spec import Column, TableSpec

GOODS_YEAR_MARKETS = TableSpec("GoodsYearMarkets", (
    Column("delivered", numpy.float64, "goods moved in the market in all the rounds so far", "good units"),
    Column("wanted", numpy.float64, "what the market's buyers asked for in all the rounds so far", "good units"),
    Column("last_offered", numpy.float64, "on offer at the price of the last round that cleared the market", "good units"),
    Column("last_delivered", numpy.float64, "goods moved in the last round that cleared the market", "good units"),
    Column("idle_years", numpy.int64, "years the market lacked bids or offers before this year, added", "years"),
    Column("last_price", numpy.float64, "the price the market's memory held when the year began; NaN: it held none", "currency units per unit"),
))
GoodsYearMarkets = GOODS_YEAR_MARKETS.make_type(__name__)

_FIRST_CAPACITY = 64


class YearMarkets:
    """The table and the rows in use; a market claims a row when it is made (`claim`) and gets its figures with `fill`."""

    def __init__(self, capacity: int = _FIRST_CAPACITY) -> None:
        self.table = GOODS_YEAR_MARKETS.new_table(GoodsYearMarkets, capacity)

    def claim(self, count: int) -> int:
        """The first of `count` new rows, which are now in use."""
        self.table = reserve_rows(self.table, count)
        first = int(self.table.row_count[0])
        self.table.row_count[0] = first + count
        return first

    def fill(self, first: int, delivered: Sequence[float], wanted: Sequence[float], last_offered: Sequence[float],
             last_delivered: Sequence[float], idle_years: Sequence[int], last_price: Sequence[float]) -> None:
        """Set the figures of the rows `first ...` (one entry per row, NaN for no price)."""
        table, last = self.table, first + len(delivered)
        table.delivered[first:last] = delivered
        table.wanted[first:last] = wanted
        table.last_offered[first:last] = last_offered
        table.last_delivered[first:last] = last_delivered
        table.idle_years[first:last] = idle_years
        table.last_price[first:last] = last_price

    def add_rounds(self, rows: numpy.ndarray, delivered: numpy.ndarray, wanted: numpy.ndarray, last_offered: numpy.ndarray,
                   last_delivered: numpy.ndarray) -> None:
        """The respend's answer for the markets in `rows` (each once): what its rounds delivered and its buyers wanted are added to the
        totals, and the last round's offered and delivered replace the last figures."""
        table = self.table
        table.delivered[rows] = table.delivered[rows] + delivered
        table.wanted[rows] = table.wanted[rows] + wanted
        table.last_offered[rows] = last_offered
        table.last_delivered[rows] = last_delivered

    def unsold(self, rows: numpy.ndarray) -> numpy.ndarray:
        """What the last round to clear each market left on offer, never below zero."""
        gap = self.table.last_offered[rows] - self.table.last_delivered[rows]
        return numpy.where(gap > 0.0, gap, 0.0)
