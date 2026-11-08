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

    def of(self, good: str) -> int:
        found = self.number.get(good)
        if found is None:
            found = self.number[good] = len(self.names)
            self.names.append(good)
        return found


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


class NeedBatch:
    """Requests collected as rows. `specs` is the spec of each need row, `owners` the request each need row belongs to."""

    def __init__(self) -> None:
        self.specs: List[NeedSpec] = []
        self.owners: List[int] = []
        self._tile: List[int] = []
        self._exponent: List[float] = []
        self._first: List[int] = []
        self._good: List[int] = []
        self._effect: List[float] = []
        self._quality: List[float] = []
        self._limit: List[float] = []
        self.requests = 0
        self.has_limits = False

    def add(self, tile_row: int, exponent: float, needs: Sequence[NeedSpec]) -> int:
        """Add a request to price `needs` at the prices of matrix row `tile_row`; returns the request's number. `needs` should be the
        tuple object a basket holds (`Basket.needs`), so its rows are found kept."""
        request = self.requests
        self.requests += 1
        _held, specs, first, goods, effects, qualities, limits, limited = basket_rows(needs)
        base = len(self._good)
        self.specs.extend(specs)
        self.owners.extend([request] * len(specs))
        self._tile.extend([tile_row] * len(specs))
        self._exponent.extend([exponent] * len(specs))
        self._first.extend([base + each for each in first])
        self._good.extend(goods)
        self._effect.extend(effects)
        self._quality.extend(qualities)
        self._limit.extend(limits)
        self.has_limits = self.has_limits or limited
        return request

    def tables(self) -> Tuple[object, object]:
        """The need and good tables of the requests added, answers empty."""
        need_count, row_count = len(self.specs), len(self._good)
        needs = NEED_ROWS.new_table(PricedNeedRows, need_count, need_count)
        needs.tile[:] = self._tile
        needs.exponent[:] = self._exponent
        needs.first_row[:] = self._first
        needs.end_row[:] = self._first[1:] + [row_count]
        needs.price_index[:] = numpy.nan
        rows = GOOD_ROWS.new_table(PricedGoodRows, row_count, row_count)
        rows.good[:] = self._good
        rows.effect[:] = self._effect
        rows.quality[:] = self._quality
        rows.limit[:] = self._limit
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
