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
    Column("way", numpy.int64, "how the first round cleared it: 0 traded in the batch, 1 did not trade (quote from the columns), 2 on `Bid` and `Offer` objects",
           "code"),
    Column("quote_price", numpy.float64, "the first round's quote price; NaN: no quote", "currency units per unit"),
    Column("quote_kind", numpy.int64, "the first round's quote kind (`goods_remember_kernel`: 0 none, 1 best unfilled bid, 2 lowest unfilled ask, 3 cost covering)",
           "code"),
    Column("bid_first", numpy.int64, "where the market's first-round bid rows start in `YearMarkets.bid_rows()`", "place"),
    Column("bid_count", numpy.int64, "how many first-round bids the market has", "count"),
    Column("first_price", numpy.float64, "the first round's price; NaN: it had none", "currency units per unit"),
    Column("left_first", numpy.int64, "where the market's offers that kept units start in `YearMarkets.left_rows()` and `left_units()`", "place"),
    Column("left_count", numpy.int64, "how many of the market's offers keep units after the rounds so far", "count"),
))
GoodsYearMarkets = GOODS_YEAR_MARKETS.make_type(__name__)

_FIRST_CAPACITY = 64


class Flat:
    """One column of numbers that grows by pieces (one good's rows after another's); `add` gives the place a piece starts at."""

    def __init__(self, dtype) -> None:
        self._dtype, self._pieces, self._total = dtype, [], 0

    def add(self, piece: numpy.ndarray) -> int:
        first = self._total
        self._pieces.append(numpy.asarray(piece, dtype=self._dtype))
        self._total += len(piece)
        return first

    def all(self) -> numpy.ndarray:
        """Every number added, in order, as one array (the same array until more is added)."""
        if len(self._pieces) != 1:
            self._pieces = [numpy.concatenate(self._pieces) if self._pieces else numpy.zeros(0, dtype=self._dtype)]
        return self._pieces[0]


class YearMarkets:
    """The table and the rows in use; a market claims a row when it is made (`claim`) and gets its figures with `fill`."""

    def __init__(self, capacity: int = _FIRST_CAPACITY) -> None:
        self.table = GOODS_YEAR_MARKETS.new_table(GoodsYearMarkets, capacity)
        self._bids, self._left_rows, self._left_units = Flat(numpy.int64), Flat(numpy.int64), Flat(numpy.float64)
        self._added: list = []
        self._added_names: list = []
        self._later: list = []
        self._bought: list = []
        self.first_round_filled = False       # false for a market made alone: its rows are not in the columns below

    def add_bid_rows(self, rows: numpy.ndarray) -> int:
        """Keep these order-table bid rows (one good's markets, market by market); the place the first of them has in `bid_rows()`."""
        return self._bids.add(rows)

    def bid_rows(self) -> numpy.ndarray:
        """Every kept bid row, in the order they were added."""
        return self._bids.all()

    def add_left_rows(self, rows: numpy.ndarray, units: numpy.ndarray) -> int:
        """Keep the order-table rows of the offers that kept units after the first round, with the units each kept (one good's markets, market
        by market); the place the first has in `left_rows()` and `left_units()`."""
        self._left_units.add(units)
        return self._left_rows.add(rows)

    def left_rows(self) -> numpy.ndarray:
        """The rows of every offer that kept units after the first round."""
        return self._left_rows.all()

    def left_units(self) -> numpy.ndarray:
        """The units each offer of `left_rows()` has left after the rounds so far (the respend's kernel changes them in place)."""
        return self._left_units.all()

    def add_bought(self, cells: numpy.ndarray, agent: numpy.ndarray, units: numpy.ndarray, money: numpy.ndarray) -> None:
        """Keep what the first round's settlement gave each buyer that bought or paid: the market's table row, the buyer's book number, the units
        received and the money paid net (zero where the buyer was not seen paying)."""
        self._bought.append((cells, agent, units, money))

    def bought(self):
        """(table row, buyer number, units, money) of every buyer the first round's settlement noted, in the order they were kept."""
        if not self._bought:
            return numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0), numpy.zeros(0)
        return tuple(numpy.concatenate([piece[each] for piece in self._bought]) for each in range(4))

    def add_added_bids(self, cells: numpy.ndarray, flexible, reference, elasticity, budget, maximum, buyers=None, tiles=None) -> None:
        """Keep the bids later rounds added: the table row of each one's market and its columns (the floor is zero), and, for a reader that
        wants `Bid` objects, the buyer and tile names of each."""
        self._added.append((cells, flexible, reference, elasticity, budget, maximum))
        self._added_names.append((buyers, tiles))

    def added_of(self, row: int):
        """(buyers, tiles, flexible, reference, elasticity, budget, maximum) of the bids later rounds added to the market at table `row`, as
        lists, in the order they were added; None when it has none."""
        found = []
        for piece, (buyers, tiles) in zip(self._added, self._added_names):
            for place in numpy.flatnonzero(piece[0] == row).tolist():
                found.append((buyers[place], tiles[place], *[float(each[place]) for each in piece[1:]]))
        return None if not found else tuple(list(each) for each in zip(*found))

    def add_later(self, cells: numpy.ndarray, quantity, price, demand, offered) -> None:
        """Keep the respend rounds' clearings: the table row of each one's market and its quantity, price (NaN: none), demand at that price
        and the units offered at it, rounds in the order they were run."""
        self._later.append((cells, quantity, price, demand, offered))

    def later_of(self, row: int) -> list:
        """The respend rounds of the market at table `row` as (quantity, price or None, demand, offered), in the order they were run."""
        return [(float(piece[1][place]), None if piece[2][place] != piece[2][place] else float(piece[2][place]), float(piece[3][place]),
                 float(piece[4][place])) for piece in self._later for place in numpy.flatnonzero(piece[0] == row).tolist()]

    def added_bids(self, cells: numpy.ndarray):
        """(pointers, flexible, reference, elasticity, budget, maximum) of the added bids of the markets at `cells`, market by market in this
        order, each market's in the order they were added."""
        if not self._added:
            return (numpy.zeros(len(cells) + 1, dtype=numpy.int64), *[numpy.zeros(0) for _each in range(5)])
        columns = [numpy.concatenate([piece[each] for piece in self._added]) for each in range(6)]
        place_of_cell = numpy.full(int(self.table.row_count[0]), -1, dtype=numpy.int64)
        place_of_cell[cells] = numpy.arange(len(cells), dtype=numpy.int64)
        place = place_of_cell[columns[0]]
        kept = numpy.flatnonzero(place >= 0)
        order = kept[numpy.argsort(place[kept], kind="stable")]
        pointers = numpy.concatenate(([0], numpy.cumsum(numpy.bincount(place[order], minlength=len(cells))))).astype(numpy.int64)
        return (pointers, *[column[order] for column in columns[1:]])

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

    def fill_first_round(self, first: int, way, price, quote_price, quote_kind, bid_first, bid_count, left_first, left_count) -> None:
        """Set how the rows `first ...` were cleared, their quotes, where their bid rows are and how many offers they keep."""
        table, last = self.table, first + len(way)
        self.first_round_filled = True
        table.way[first:last] = way
        table.first_price[first:last] = price
        table.left_first[first:last] = left_first
        table.quote_price[first:last] = quote_price
        table.quote_kind[first:last] = quote_kind
        table.bid_first[first:last] = bid_first
        table.bid_count[first:last] = bid_count
        table.left_count[first:last] = left_count

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
