"""The memory's notes after a year's clearings written as columns (`goods_memory_kernels.py`), for `year_goods`.

The caller hands one entry per goods market in sorted (good, area) order; the markets are numbered first (as the wrappers did, one
by one in that order, so any unnumbered market gets the number it would have), the columns are read from and written to the
memory's goods table, and the memory's write stamps move once, as the wrapper calls moved them."""
from typing import Optional, Sequence

import numpy

from .goods_memory_kernels import NO_KIND, decay_unseen_volumes, note_markets, note_volumes
from .market_memory import (USUAL_PRICE_SPEED, VOLUME_WEIGHT_SPEED, note_age_and_kind_written, note_written)
from .market_table_kernels import note_year_traded
from .market_table_specs import HELD_QUOTE_KIND

# A good sold only at a token price would otherwise be remembered at a thousandth of last year's price
# every year until it underflows; nothing is remembered below this share of its opening price.
PRICE_MEMORY_FLOOR_SHARE = 1e-9


def rows_of(memory, keys: Sequence[str]) -> numpy.ndarray:
    """The market number of each key (`good|area`), numbering a new market on the way."""
    tables = memory.tables
    return numpy.array([tables.goods_row_for_write(key) for key in keys], dtype=numpy.int64)


def last_year_columns(memory, rows: numpy.ndarray):
    """(was the market's price a quote?, its usual volume or 0.0) per row, as the memory stands now."""
    table = memory.tables.goods_table
    volume = table.volume_weight[rows]
    return ((table.held[rows] & HELD_QUOTE_KIND) != 0).tolist(), numpy.where(numpy.isnan(volume), 0.0, volume).tolist()


def write_markets(memory, rows: numpy.ndarray, signal: Sequence[Optional[float]], kind_numbers: Sequence[int], from_trade: Sequence[bool],
                  cleared_price: Sequence[Optional[float]], delivered: Sequence[float], opening: Sequence[Optional[float]]) -> None:
    """`note_markets` for the markets in `rows`, then the year's trade ages (`MarketMemory.note_trading` of the markets that delivered).
    `signal`, `cleared_price` and `opening` use None for none; `kind_numbers` the table's number of the quote kind, or NO_KIND."""
    tables = memory.tables
    table = tables.goods_table
    nan = numpy.nan
    note_markets(
        table.price, table.usual_price, table.cleared_price, table.held, table.quote_kind, table.order_price, table.order_usual_price,
        table.order_cleared_price, table.order_quote_kind, tables.next_order, tables.member_count, rows,
        numpy.array([nan if each is None else each for each in signal], dtype=float), numpy.array(kind_numbers, dtype=numpy.int64),
        numpy.array(from_trade, dtype=numpy.bool_), numpy.array([nan if each is None else each for each in cleared_price], dtype=float),
        numpy.array(delivered, dtype=float), numpy.array([nan if each is None else each for each in opening], dtype=float),
        PRICE_MEMORY_FLOOR_SHARE, USUAL_PRICE_SPEED)
    note_written()
    note_year_traded(table, rows[numpy.array(delivered, dtype=float) > 0.0], tables.next_order, tables.member_count)
    note_age_and_kind_written()


def kind_number(memory, kind: Optional[str]) -> int:
    """The quote kind table's number of a kind name (NO_KIND for None)."""
    return NO_KIND if kind is None else memory.tables.kind_number(kind)


def write_volumes(memory, rows: numpy.ndarray, quantity: Sequence[float]) -> None:
    """`MarketMemory.note_volume` for each market in `rows` in this order, then the usual volume of every other market moves toward zero."""
    tables = memory.tables
    table = tables.goods_table
    note_volumes(table.volume_weight, table.order_volume_weight, tables.next_order, tables.member_count, rows,
                 numpy.array(quantity, dtype=float), VOLUME_WEIGHT_SPEED)
    count = int(table.row_count[0])
    seen = numpy.zeros(count, dtype=numpy.bool_)
    seen[rows] = True
    decay_unseen_volumes(table.volume_weight, count, seen, VOLUME_WEIGHT_SPEED)
