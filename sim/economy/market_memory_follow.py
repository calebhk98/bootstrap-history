"""The market memory across a new partition of market areas: the goods markets are renumbered by table, not rebuilt as dicts.

`follow_goods_markets` does what `market_areas_follow._moved` does to the memory's dicts: a market of a redrawn good is dropped,
and each new market takes the figures of the old market that held its anchor tile. Markets that are not a redrawn good's (a
good with no market before, a key that is no market of one) keep their numbers and their place in each store's order; the new
markets are numbered after them and enter each store in the order of the areas (so a store lists the surviving markets first,
then the redrawn goods' markets, as the dict did)."""
from typing import Mapping, NamedTuple

import numpy

from .market_memory import MarketMemory, note_age_and_kind_written
from .market_table_kernels import remap_goods_markets
from .market_table_specs import KEY_SEPARATOR


class GoodsRemap(NamedTuple):
    """How the goods markets were renumbered: the new row of each old row (-1: dropped), and pair `p`: new market `new_rows[p]` takes
    the figures of old market `old_rows[p]` (-1: the old one was never numbered). Applied to a column held beside the table
    (`merchant_figures.MarketFigures.follow`)."""
    old_to_new: numpy.ndarray
    new_rows: numpy.ndarray
    old_rows: numpy.ndarray


def follow_goods_markets(memory: MarketMemory, follows: Mapping[str, Mapping[str, str]], old_ids: Mapping[str, frozenset]) -> GoodsRemap:
    """`follows` is {good: {new area id: old area id}}, `old_ids` {good: the old area ids of that good}. Returns the renumbering."""
    tables = memory.tables
    old_numbering, old_table = tables.goods_markets, tables.goods_table
    names = old_numbering.names
    keep = numpy.ones(len(names), dtype=numpy.bool_)
    for row, name in enumerate(names):
        first, _separator, area_id = name.partition(KEY_SEPARATOR)
        if first in follows and area_id in old_ids[first]:
            keep[row] = False
    numbering, old_to_new = old_numbering.compacted(keep)
    new_keys, old_keys = [], []
    for good, new_to_old in follows.items():
        for new_id, old_id in new_to_old.items():
            new_keys.append(good + KEY_SEPARATOR + new_id)
            old_keys.append(good + KEY_SEPARATOR + old_id)
    numbering.admit(new_keys)
    new_table = tables.blank_goods_table(numbering)
    new_rows = numpy.array([numbering.number(key) for key in new_keys], dtype=numpy.int64)
    old_rows = numpy.array([-1 if old_numbering.find(key) is None else old_numbering.number(key) for key in old_keys],
                           dtype=numpy.int64)
    remap_goods_markets(old_table, new_table, old_to_new, new_rows, old_rows, tables.next_order, tables.member_count)
    tables.install_goods_markets(numbering, new_table)
    note_age_and_kind_written()
    return GoodsRemap(old_to_new, new_rows, old_rows)
