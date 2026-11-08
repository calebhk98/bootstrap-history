"""The year's bids of every goods market as one grouped table, for the entry rules.

`YearBids` holds all markets' bids in one set of columns, markets in sorted (good, area) order and each market's rows together: the
first round's bids in the order they reached the book, then the bids later respend rounds added, then (`with_standing`) the standing
bids. A market's rows are `start[index]` up to `start[index + 1]`. The six figure columns are `bid_columns.BidColumns`:
    floor, flexible, reference, elasticity, budget, maximum    (documented in bid_columns.py)

Fields:
    markets    (good, area) of each market, sorted
    start      first row of each market, one more than the markets (the last is the row count)   rows
    columns    the six figure columns over all rows
    index      market -> its place in `markets`

Built once a year by `build` from the cleared markets, reading a market on the order tables from the table's columns in one gather and the
added bids from the lists the respend kernel wrote; a reader takes a market's rows as slices (`columns_at`, no copy) or hands the whole
block and the market places to a kernel (`year_bids_kernels`).
"""
import bisect
from typing import Dict, Mapping, Sequence, Tuple

import numpy

from .bid_columns import BidColumns, columns_of
from .goods_respend_rows import table_columns
from .year_bids_kernels import demand_at_many

Market = Tuple[str, str]


class YearBids:
    """The year's bids in one table (see the module docstring)."""

    def __init__(self, markets: Sequence[Market], start: numpy.ndarray, columns: BidColumns):
        self.markets = list(markets)
        self.start = start
        self.columns = columns
        self.index: Dict[Market, int] = {market: place for place, market in enumerate(self.markets)}

    def __len__(self) -> int:
        return len(self.markets)

    def count(self, place: int) -> int:
        """How many bids market number `place` has."""
        return int(self.start[place + 1] - self.start[place])

    def columns_at(self, place: int) -> BidColumns:
        """Market number `place`'s bids as column views (no copy)."""
        first, last = int(self.start[place]), int(self.start[place + 1])
        return BidColumns(*(each[first:last] for each in self.columns))

    def demand_at_many(self, places: Sequence[int], prices: Sequence[float], prices_now: Sequence[float]) -> numpy.ndarray:
        """`bid_columns.demand_at` of market number `places[question]` at `prices[question]`, the bids made at `prices_now[question]`, for each
        question, in one call."""
        return demand_at_many(*self.columns, self.start, numpy.array(places, dtype=numpy.int64), numpy.array(prices, dtype=numpy.float64),
                              numpy.array(prices_now, dtype=numpy.float64))

    def with_standing(self, standing: Mapping[Market, Sequence]) -> "YearBids":
        """The block with each market's standing bids (`Bid` objects, a project's draw settled outside the book) after its other bids; a market
        only they name is added, in its sorted place. `self` when there are none. The standing bids go into each column in one insertion."""
        named = sorted(market for market, bids in standing.items() if bids)
        if not named:
            return self
        inserts = []      # (row to insert before, market, whether the block has the market, the bids' columns)
        fresh = []        # (place among the old markets the new market sorts before, market)
        for market in named:
            piece = columns_of(list(standing[market]))
            place = self.index.get(market)
            if place is not None:
                inserts.append((int(self.start[place + 1]), market, True, piece))
            else:
                before = bisect.bisect_left(self.markets, market)
                fresh.append((before, market))
                inserts.append((int(self.start[before]), market, False, piece))
        inserts.sort(key=lambda each: each[:2])        # rows come in market order, so a tie in the row is settled by the market
        pieces = [each[3] for each in inserts]
        counts = numpy.diff(self.start)
        for _row, market, held, piece in inserts:
            if held:
                counts[self.index[market]] += len(piece.floor)
        markets = list(self.markets)
        if fresh:
            counts = numpy.insert(counts, [before for before, _market in fresh],
                                  [len(standing[market]) for _before, market in fresh])
            for before, market in sorted(fresh, reverse=True):
                markets.insert(before, market)
        rows = numpy.array([each[0] for each in inserts for _bid in range(len(each[3].floor))], dtype=numpy.int64)
        inserted = BidColumns(*(numpy.insert(self.columns[each], rows, numpy.concatenate([piece[each] for piece in pieces]))
                                for each in range(6)))
        return YearBids(markets, _starts(counts), inserted)


def _starts(counts: Sequence[int]) -> numpy.ndarray:
    """The first row of each group of the given sizes, and the total after the last."""
    start = numpy.zeros(len(counts) + 1, dtype=numpy.int64)
    numpy.cumsum(counts, out=start[1:])
    return start


def _stack(pieces: Sequence[BidColumns]) -> BidColumns:
    if not pieces:
        return BidColumns(*[numpy.zeros(0) for _each in range(6)])
    return BidColumns(*(numpy.concatenate([piece[each] for piece in pieces]) for each in range(6)))


def of_mapping(bids_by_market: Mapping[Market, Sequence]) -> YearBids:
    """A block from a mapping of market to bids (`Bid` objects or `MarketBids`): a test, or a year whose bids are not on the tables. Markets in
    sorted order."""
    markets = sorted(bids_by_market)
    pieces = [columns_of(bids_by_market[market]) for market in markets]
    return YearBids(markets, _starts([len(piece.floor) for piece in pieces]), _stack(pieces))


def build(left_markets: Mapping[Market, object]) -> YearBids:
    """The block of the cleared markets (`goods_respend_year.LeftMarket`): a market on the order tables is read from the table's columns,
    a market on the objects from its `Bid`s, and each market's added bids follow its first-round bids."""
    markets = sorted(left_markets)
    lefts = [left_markets[market] for market in markets]
    columns = table_columns(left_markets, markets)
    if columns is not None:
        return _build_from_table(markets, lefts, columns)
    rows_of = [left.rows for left in lefts]
    selected = [None if each is None else each.bid_array for each in rows_of]
    first_counts = [len(left.bids) if each is None else len(each) for left, each in zip(lefts, selected)]
    added_lists = [left.added for left in lefts]
    added_counts = [0 if each is None else len(each) for each in added_lists]
    on_tables = [(place, each) for place, each in enumerate(selected) if each is not None]
    objects = [place for place, each in enumerate(selected) if each is None]
    orders = next((each.orders for each in rows_of if each is not None), None)
    table = orders.tables()[0] if orders is not None else None
    counts = numpy.array(first_counts, dtype=numpy.int64) + numpy.array(added_counts, dtype=numpy.int64)
    start = _starts(counts)
    total = int(start[-1])
    columns = [numpy.zeros(total) for _each in range(6)]
    first_start = start[:-1]
    if on_tables:
        rows = numpy.concatenate([each for _place, each in on_tables])
        places = numpy.array([place for place, _each in on_tables], dtype=numpy.int64)
        sizes = numpy.array([len(each) for _place, each in on_tables], dtype=numpy.int64)
        within = numpy.arange(len(rows), dtype=numpy.int64) - numpy.repeat(_starts(sizes)[:-1], sizes)
        target = numpy.repeat(first_start[places], sizes) + within
        for column, name in zip(columns, ("floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget", "maximum_price")):
            column[target] = getattr(table, name)[rows]
    for place in objects:
        left = lefts[place]
        if first_counts[place]:
            piece = columns_of(list(left.bids))
            first = int(first_start[place])
            for column, each in zip(columns, piece):
                column[first:first + first_counts[place]] = each
    added_places = [place for place in range(len(markets)) if added_counts[place]]
    if added_places:
        flexible, reference, elasticity, budget, maximum = ([] for _each in range(5))
        for place in added_places:
            added = added_lists[place]
            flexible += added.flexible
            reference += added.reference
            elasticity += added.elasticity
            budget += added.budget
            maximum += added.maximum
        sizes = numpy.array([added_counts[place] for place in added_places], dtype=numpy.int64)
        within = numpy.arange(int(sizes.sum()), dtype=numpy.int64) - numpy.repeat(_starts(sizes)[:-1], sizes)
        where = numpy.array(added_places, dtype=numpy.int64)
        target = numpy.repeat(first_start[where] + numpy.array(first_counts, dtype=numpy.int64)[where], sizes) + within
        # the floor of an added bid is zero, which the zero-filled column already holds
        for column, values in zip(columns[1:], (flexible, reference, elasticity, budget, maximum)):
            column[target] = numpy.array(values, dtype=numpy.float64)
    return YearBids(markets, start, BidColumns(*columns))


def _ranges(first: numpy.ndarray, count: numpy.ndarray) -> numpy.ndarray:
    """The places `first[i] .. first[i] + count[i] - 1` for every i, one after another."""
    stops = numpy.cumsum(count)
    return numpy.repeat(first - (stops - count), count) + numpy.arange(int(stops[-1]) if len(stops) else 0, dtype=numpy.int64)


def _build_from_table(markets, lefts, columns) -> YearBids:
    """`build` for markets that share the year's table (`goods_year_markets.YearMarkets`): the first round's bids of the markets on the order
    tables are gathered from the table's bid rows and the added bids are the table's columns, both in one pass; a market on the objects
    contributes its `Bid`s."""
    year_markets, cells, on_tables = columns
    table = year_markets.table
    first_counts = table.bid_count[cells].copy()
    objects = numpy.flatnonzero(~on_tables).tolist()
    for place in objects:
        first_counts[place] = len(lefts[place].bids)
    added_pointers, *added = year_markets.added_bids(cells)
    start = _starts(first_counts + numpy.diff(added_pointers))
    figures = [numpy.zeros(int(start[-1])) for _each in range(6)]
    here = numpy.flatnonzero(on_tables)
    if len(here):
        orders = lefts[int(here[0])].rows.orders
        rows = year_markets.bid_rows()[_ranges(table.bid_first[cells[here]], first_counts[here])]
        target = _ranges(start[here], first_counts[here])
        bids = orders.tables()[0]
        for column, name in zip(figures, ("floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget", "maximum_price")):
            column[target] = getattr(bids, name)[rows]
    for place in objects:
        if first_counts[place]:
            first = int(start[place])
            for column, each in zip(figures, columns_of(list(lefts[place].bids))):
                column[first:first + int(first_counts[place])] = each
    if len(added[0]):
        target = _ranges(start[:-1] + first_counts, numpy.diff(added_pointers))
        for column, values in zip(figures[1:], added):      # the floor of an added bid is zero, which the zero-filled column already holds
            column[target] = values
    return YearBids(markets, start, BidColumns(*figures))


def of(bids) -> YearBids:
    """The block of what a caller hands the entry rules: the block itself, or a mapping of market to bids (`of_mapping`)."""
    return bids if isinstance(bids, YearBids) else of_mapping(bids)
