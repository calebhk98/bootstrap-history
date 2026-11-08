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
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy

from .bid_columns import BidColumns, columns_of
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
        only they name is added. `self` when there are none."""
        if not standing:
            return self
        markets = sorted(set(self.markets) | set(standing))
        pieces: List[BidColumns] = []
        counts = []
        for market in markets:
            place = self.index.get(market)
            parts = []
            if place is not None:
                parts.append(self.columns_at(place))
            if standing.get(market):
                parts.append(columns_of(list(standing[market])))
            joined = BidColumns(*(numpy.concatenate([part[each] for part in parts]) for each in range(6)))
            pieces.append(joined)
            counts.append(len(joined.floor))
        return YearBids(markets, _starts(counts), _stack(pieces))


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
    first_counts, added_counts = [], []
    on_tables, objects, table = [], [], None
    for place, market in enumerate(markets):
        left = left_markets[market]
        added = left.added
        added_counts.append(0 if added is None else len(added))
        rows = left.rows
        if rows is not None:
            selected = rows.bid_array
            on_tables.append((place, selected))
            first_counts.append(len(selected))
            table = rows.orders
        else:
            objects.append(place)
            first_counts.append(len(left.bids))
    table = table.tables()[0] if table is not None else None
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
        left = left_markets[markets[place]]
        if first_counts[place]:
            piece = columns_of(list(left.bids))
            first = int(first_start[place])
            for column, each in zip(columns, piece):
                column[first:first + first_counts[place]] = each
    added_places = [place for place in range(len(markets)) if added_counts[place]]
    if added_places:
        flexible, reference, elasticity, budget, maximum = ([] for _each in range(5))
        for place in added_places:
            added = left_markets[markets[place]].added
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


def of(bids) -> YearBids:
    """The block of what a caller hands the entry rules: the block itself, or a mapping of market to bids (`of_mapping`)."""
    return bids if isinstance(bids, YearBids) else of_mapping(bids)
