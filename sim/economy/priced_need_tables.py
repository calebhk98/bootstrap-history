"""The household baskets' needs priced on tiles, as two tables: what `need_basket.PricedNeed` objects hold, one row per need and one per
good of a need (`priced_need_kernel.price_needs` fills them from a matrix of prices, tiles by goods).

A `NeedBatch` collects any number of (tile, basket) requests: each request adds a row per need and a row per good the need names, in the
order of `NeedSpec.goods`. The columns that come from the specs (`good`, `effect`, `quality`, `limit`) are cached per spec (`spec_rows`,
which a basket shares with every other basket holding the same spec object); the request adds its tile and exponent. The columns the
kernel writes (`price`, `priced`, `share`, `ceiling`; `need_priced`, `price_index`) start empty. A good number is the good's place in
`GOODS`, the one numbering of the process (it only grows), the column of the price matrix.

`priced_needs.priced_need_of` makes a `PricedNeed` object from an answered row: the edge for a reader that wants objects. Nothing in the
tables is a default: a good with no price has `priced` 0 and a NaN `price`."""
from typing import Dict, List, Optional, Sequence, Tuple

import numpy

from sim.compiled_tables.spec import Column, TableSpec
from sim.world.need_basket import NeedSpec

NEED_ROWS = TableSpec("PricedNeedRows", (
    Column("tile", numpy.int64, "row of the price matrix the need is priced at (the tile's prices)", "matrix row"),
    Column("exponent", numpy.float64, "one minus the basket's substitution elasticity", "dimensionless"),
    Column("first_row", numpy.int64, "first row of the need's goods in the good rows", "row"),
    Column("end_row", numpy.int64, "one past the last row of the need's goods", "row"),
    Column("need_priced", numpy.uint8, "1 when at least one good of the need has a price (answer)", "flag"),
    Column("price_index", numpy.float64, "money per need unit of the mix the household buys (answer; NaN when the need is not priced)",
           "money per need unit"),
))
PricedNeedRows = NEED_ROWS.make_type(__name__)

GOOD_ROWS = TableSpec("PricedGoodRows", (
    Column("good", numpy.int64, "number of the good in GOODS (the column of the price matrix)", "good number"),
    Column("effect", numpy.float64, "need units one unit of the good gives", "need units per unit"),
    Column("quality", numpy.float64, "quality factor the buyer values (1 when the good declares none)", "factor"),
    Column("limit", numpy.float64, "largest share of the need's units the good can meet (NaN when none)", "share of need units"),
    Column("price", numpy.float64, "offered price of the good on the tile (answer; NaN when none)", "money per unit"),
    Column("priced", numpy.uint8, "1 when the good has a price and gives need units, so it takes part in the mix (answer)", "flag"),
    Column("share", numpy.float64, "share of the need's spending the good takes (answer; 0 when not priced)", "share"),
    Column("ceiling", numpy.float64, "price a buyer stops buying the good above (answer; inf when none)", "money per unit"),
))
PricedGoodRows = GOOD_ROWS.make_type(__name__)


class GoodNumbers:
    """Names to numbers, growing: the order goods were first met. A number is never reused."""

    def __init__(self) -> None:
        self.number: Dict[str, int] = {}
        self.names: List[str] = []
        self._array: Optional[numpy.ndarray] = None
        self._rank: Optional[numpy.ndarray] = None

    def of(self, good: str) -> int:
        found = self.number.get(good)
        if found is None:
            found = self.number[good] = len(self.names)
            self.names.append(good)
        return found

    def name_array(self) -> numpy.ndarray:
        """The names as an object array indexed by good number, so a column of good numbers becomes names in one take."""
        if self._array is None or len(self._array) != len(self.names):
            self._array = numpy.array(self.names, dtype=object)
        return self._array

    def rank_array(self) -> numpy.ndarray:
        """Each good's place among the names in sorted order, indexed by good number."""
        if self._rank is None or len(self._rank) != len(self.names):
            order = numpy.argsort(self.name_array(), kind="stable")
            self._rank = numpy.empty(len(order), dtype=numpy.int64)
            self._rank[order] = numpy.arange(len(order))
        return self._rank


GOODS = GoodNumbers()

_SPEC_ROWS: Dict[int, tuple] = {}      # id(spec) -> (spec, goods, effects, qualities, limits); the spec is held so its id is not reused
_SPEC_ROWS_LIMIT = 8192


def spec_rows(spec: NeedSpec) -> tuple:
    """(spec, good numbers, effects, qualities, limits) of a need's goods, as lists in the spec's order; kept by the spec object."""
    found = _SPEC_ROWS.get(id(spec))
    if found is None:
        if len(_SPEC_ROWS) >= _SPEC_ROWS_LIMIT:
            _SPEC_ROWS.clear()
        quality, limit = dict(spec.qualities), dict(spec.share_limits)
        found = _SPEC_ROWS[id(spec)] = (spec, [GOODS.of(good) for good, _effect in spec.goods], [effect for _good, effect in spec.goods],
                                        [quality.get(good, 1.0) for good, _effect in spec.goods],
                                        [limit.get(good, numpy.nan) for good, _effect in spec.goods])
    return found


_BASKET_ROWS: Dict[int, tuple] = {}      # id(needs tuple) -> (needs, rows); the tuple is held so its id is not reused


def basket_rows(needs: Sequence[NeedSpec]) -> tuple:
    """A basket's needs as list columns, kept by the needs tuple object (cohorts of one basket share it): (needs, specs, first row of each
    need relative to the basket's first row, good numbers, effects, qualities, limits, whether any good has a share limit)."""
    found = _BASKET_ROWS.get(id(needs))
    if found is not None:
        return found
    if len(_BASKET_ROWS) >= _SPEC_ROWS_LIMIT:
        _BASKET_ROWS.clear()
    first, goods, effects, qualities, limits = [], [], [], [], []
    for spec in needs:
        _spec, spec_goods, spec_effects, spec_qualities, spec_limits = spec_rows(spec)
        first.append(len(goods))
        goods.extend(spec_goods)
        effects.extend(spec_effects)
        qualities.extend(spec_qualities)
        limits.extend(spec_limits)
    found = _BASKET_ROWS[id(needs)] = (needs, tuple(needs), first, goods, effects, qualities, limits, any(spec.share_limits for spec in needs))
    return found


_BASKET_ARRAYS: Dict[int, tuple] = {}      # id(needs tuple) -> (needs, arrays); the tuple is held so its id is not reused


def basket_arrays(needs: Sequence[NeedSpec]) -> tuple:
    """`basket_rows` of the needs as numpy arrays, kept by the needs tuple object: (first row of each need, good numbers, effects, qualities,
    limits)."""
    found = _BASKET_ARRAYS.get(id(needs))
    if found is not None:
        return found[1]
    if len(_BASKET_ARRAYS) >= _SPEC_ROWS_LIMIT:
        _BASKET_ARRAYS.clear()
    _held, _specs, first, goods, effects, qualities, limits, _limited = basket_rows(needs)
    arrays = (numpy.array(first, dtype=numpy.int64), numpy.array(goods, dtype=numpy.int64), numpy.array(effects, dtype=numpy.float64),
              numpy.array(qualities, dtype=numpy.float64), numpy.array(limits, dtype=numpy.float64))
    _BASKET_ARRAYS[id(needs)] = (needs, arrays)
    return arrays


class NeedBatch:
    """Requests collected, written as rows by `tables`. `specs` is the spec of each need row, `owners` the request each need row belongs to."""

    def __init__(self) -> None:
        self.specs: List[NeedSpec] = []
        self._requests: List[tuple] = []        # (tile row, exponent, `basket_arrays` of the needs) of each request
        self.requests = 0
        self.has_limits = False

    @property
    def owners(self) -> List[int]:
        """The request of each need row."""
        counts = numpy.fromiter((len(arrays[0]) for _tile, _exponent, arrays in self._requests), numpy.int64, self.requests)
        return numpy.repeat(numpy.arange(self.requests, dtype=numpy.int64), counts).tolist()

    def add(self, tile_row: int, exponent: float, needs: Sequence[NeedSpec]) -> int:
        """Add a request to price `needs` at the prices of matrix row `tile_row`; returns the request's number. `needs` should be the
        tuple object a basket holds (`Basket.needs`), so its rows are found kept."""
        request = self.requests
        self.requests += 1
        _held, specs, _first, _goods, _effects, _qualities, _limits, limited = basket_rows(needs)
        self._requests.append((tile_row, exponent, basket_arrays(needs)))
        self.specs.extend(specs)
        self.has_limits = self.has_limits or limited
        return request

    def tables(self) -> Tuple[object, object]:
        """The need and good tables of the requests added, answers empty."""
        count = self.requests
        arrays = [each[2] for each in self._requests]
        need_counts = numpy.fromiter((len(each[0]) for each in arrays), numpy.int64, count)
        row_counts = numpy.fromiter((len(each[1]) for each in arrays), numpy.int64, count)
        need_count, row_count = int(need_counts.sum()), int(row_counts.sum())
        needs = NEED_ROWS.new_table(PricedNeedRows, need_count, need_count)
        needs.tile[:] = numpy.repeat(numpy.fromiter((each[0] for each in self._requests), numpy.int64, count), need_counts)
        needs.exponent[:] = numpy.repeat(numpy.fromiter((each[1] for each in self._requests), numpy.float64, count), need_counts)
        first = numpy.concatenate([each[0] for each in arrays]) if count else numpy.zeros(0, dtype=numpy.int64)
        needs.first_row[:] = first + numpy.repeat(numpy.cumsum(row_counts) - row_counts, need_counts)
        needs.end_row[:need_count - 1] = needs.first_row[1:]
        if need_count:
            needs.end_row[need_count - 1] = row_count
        needs.price_index[:] = numpy.nan
        rows = GOOD_ROWS.new_table(PricedGoodRows, row_count, row_count)
        for place, column in enumerate((rows.good, rows.effect, rows.quality, rows.limit), start=1):
            if count:
                column[:] = numpy.concatenate([each[place] for each in arrays])
        rows.price[:] = numpy.nan
        rows.ceiling[:] = numpy.inf
        return needs, rows


def price_matrix(tile_prices: Sequence) -> numpy.ndarray:
    """Tiles by goods: row `i` holds `tile_prices[i]` (a mapping good -> price, or None for a tile with no prices) at every good of `GOODS`,
    NaN where the tile has none."""
    matrix = numpy.full((len(tile_prices), len(GOODS.names)), numpy.nan)
    number = GOODS.number
    for row, prices in enumerate(tile_prices):
        for good, price in (prices or {}).items():
            place = number.get(good)
            if place is not None and price is not None:
                matrix[row, place] = price
    return matrix
