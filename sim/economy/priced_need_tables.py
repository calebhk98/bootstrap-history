"""The household basket's needs priced on a tile, as two tables: what `need_basket.PricedNeed` objects hold, one row per need and one per
good of a need (`priced_need_kernel.price_needs` fills them from a price vector).

A basket is packed once (`pack_needs`): a row per need, a row per good a need names, in the order of `NeedSpec.goods`; the columns that
come from the specs (`good`, `effect`, `quality`, `limit`) stay as packed, the columns the kernel writes (`price`, `priced`, `share`,
`ceiling`; `need_priced`, `price_index`) are fresh arrays for each tile (`with_answers`). A good number is the place of the good in the
pack's sorted goods (`NeedPack.goods`), the index into the price vector a caller makes for a tile.

`priced_needs_of` makes the `PricedNeed` objects from the answered tables: the edge for a reader that wants objects (the screens, mods,
tests and the year's readers not yet on the tables). Nothing in the tables is a default: a good with no price has `priced` 0 and a NaN
`price`."""
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy

from sim.compiled_tables.spec import Column, TableSpec
from sim.world.need_basket import NeedSpec, PricedNeed

NEED_ROWS = TableSpec("PricedNeedRows", (
    Column("first_row", numpy.int64, "first row of the need's goods in the good rows", "row"),
    Column("end_row", numpy.int64, "one past the last row of the need's goods", "row"),
    Column("need_priced", numpy.uint8, "1 when at least one good of the need has a price (answer)", "flag"),
    Column("price_index", numpy.float64, "money per need unit of the mix the household buys (answer; NaN when the need is not priced)",
           "money per need unit"),
))
PricedNeedRows = NEED_ROWS.make_type(__name__)

GOOD_ROWS = TableSpec("PricedGoodRows", (
    Column("good", numpy.int64, "place of the good in the pack's goods (the index into a price vector)", "good number"),
    Column("effect", numpy.float64, "need units one unit of the good gives", "need units per unit"),
    Column("quality", numpy.float64, "quality factor the buyer values (1 when the good declares none)", "factor"),
    Column("limit", numpy.float64, "largest share of the need's units the good can meet (NaN when none)", "share of need units"),
    Column("price", numpy.float64, "offered price of the good on the tile (answer; NaN when none)", "money per unit"),
    Column("priced", numpy.uint8, "1 when the good has a price and gives need units, so it takes part in the mix (answer)", "flag"),
    Column("share", numpy.float64, "share of the need's spending the good takes (answer; 0 when not priced)", "share"),
    Column("ceiling", numpy.float64, "price a buyer stops buying the good above (answer; inf when none)", "money per unit"),
))
PricedGoodRows = GOOD_ROWS.make_type(__name__)


@dataclass(frozen=True)
class NeedPack:
    """A basket's needs as rows. `specs` are the basket's `NeedSpec`s in order, `goods` the sorted goods they name (the numbering of a
    price vector), `needs` and `rows` the tables with their answer columns empty."""
    specs: Tuple[NeedSpec, ...]
    goods: Tuple[str, ...]
    needs: object
    rows: object
    has_limits: bool          # whether any good of any need has a share limit (the kernel searches for them only then)

    def with_answers(self) -> Tuple[object, object]:
        """Copies of the two tables with fresh answer columns, ready for one kernel call."""
        row_count = int(self.rows.row_count[0])
        need_count = int(self.needs.row_count[0])
        needs = self.needs._replace(need_priced=numpy.zeros(need_count, dtype=numpy.uint8), price_index=numpy.full(need_count, numpy.nan))
        rows = self.rows._replace(price=numpy.full(row_count, numpy.nan), priced=numpy.zeros(row_count, dtype=numpy.uint8),
                                  share=numpy.zeros(row_count), ceiling=numpy.full(row_count, numpy.inf))
        return needs, rows


def pack_needs(specs: Sequence[NeedSpec]) -> NeedPack:
    """The needs `specs` as tables (the answers are filled in per tile by the kernel)."""
    specs = tuple(specs)
    goods = tuple(sorted({good for spec in specs for good, _effect in spec.goods}))
    number = {good: place for place, good in enumerate(goods)}
    first, end = [], []
    good_numbers, effects, qualities, limits = [], [], [], []
    for spec in specs:
        first.append(len(good_numbers))
        quality = dict(spec.qualities)
        limit = dict(spec.share_limits)
        for good, effect in spec.goods:
            good_numbers.append(number[good])
            effects.append(effect)
            qualities.append(quality.get(good, 1.0))
            limits.append(limit.get(good, numpy.nan))
        end.append(len(good_numbers))
    needs = NEED_ROWS.new_table(PricedNeedRows, len(specs), len(specs))
    needs.first_row[:] = first
    needs.end_row[:] = end
    rows = GOOD_ROWS.new_table(PricedGoodRows, len(good_numbers), len(good_numbers))
    rows.good[:] = good_numbers
    rows.effect[:] = effects
    rows.quality[:] = qualities
    rows.limit[:] = limits
    return NeedPack(specs, goods, needs, rows, any(spec.share_limits for spec in specs))


def priced_needs_of(pack: NeedPack, needs, rows, with_ceilings: bool = True) -> List[PricedNeed]:
    """The `PricedNeed` of each priced need of an answered pair of tables, in the pack's order: what `need_basket.need_prices` returns."""
    found = []
    price, effect, share, ceiling = rows.price.tolist(), rows.effect.tolist(), rows.share.tolist(), rows.ceiling.tolist()
    priced, first, end = rows.priced.tolist(), needs.first_row.tolist(), needs.end_row.tolist()
    index, need_priced = needs.price_index.tolist(), needs.need_priced.tolist()
    names = pack.goods
    good = rows.good.tolist()
    for position, spec in enumerate(pack.specs):
        if not need_priced[position]:
            continue
        kept = [row for row in range(first[position], end[position]) if priced[row]]
        found.append(PricedNeed(spec, index[position], tuple((names[good[row]], price[row], effect[row], share[row]) for row in kept),
                                tuple(ceiling[row] for row in kept) if with_ceilings else ()))
    return found


def price_vector(pack: NeedPack, price_of) -> numpy.ndarray:
    """The pack's goods' prices as a vector in the pack's good numbering: `price_of(good)` is None for a good with no price (NaN here)."""
    found = (price_of(good) for good in pack.goods)
    return numpy.array([numpy.nan if price is None else price for price in found], dtype=numpy.float64)
