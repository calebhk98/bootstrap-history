"""A good's markets cut out of the order tables in one kernel call: which bid and offer rows are the good's, the markets they
make up in the order they clear (area name), each row's market place, the rows grouped by market, and the per-market flags the
batch and the markets' memory read.

`goods_table_group.rows_of_good` and `batch_flags`, and `goods_good_clear.flags_by_market`, were a chain of numpy calls per good
(`flatnonzero`, `unique`, `searchsorted`, `bincount`, `argsort`); this is the same rules over the same columns in one pass."""
import numpy

from sim.jit import njit


@njit
def _rows_of_good(good_column, total, good_id):
    count = 0
    for row in range(total):
        if good_column[row] == good_id:
            count += 1
    rows = numpy.empty(count, dtype=numpy.int64)
    found = 0
    for row in range(total):
        if good_column[row] == good_id:
            rows[found] = row
            found += 1
    return rows


@njit
def _grouped(rows, position, groups):
    """The rows grouped by their group's place, arrival order kept inside a group, and where each group starts."""
    pointers = numpy.zeros(groups + 1, dtype=numpy.int64)
    for each in position:
        pointers[each + 1] += 1
    for group in range(groups):
        pointers[group + 1] += pointers[group]
    cursor = pointers[:groups].copy()
    grouped = numpy.empty(len(rows), dtype=numpy.int64)
    for place in range(len(rows)):
        grouped[cursor[position[place]]] = rows[place]
        cursor[position[place]] += 1
    return grouped, pointers


@njit
def good_rows(bids, offers, good_id, market_area, area_rank, is_edge, batchable):
    """(markets, bid_rows, bid_position, offer_rows, offer_position, bid_grouped, bid_ptr, offer_grouped, offer_ptr, batch_flags,
    offered, has_units, funded) of the good `good_id`.

    `markets` are the good's goods market ids in clearing order (their area's name rank, `area_rank[market_area[market]]`);
    `bid_rows` and `offer_rows` the rows of its bids and offers in table order, `*_position` the place in `markets` of each row's
    market, `*_grouped` and `*_ptr` the rows market by market (arrival order inside a market). `batch_flags` per market: it has
    units on offer, no book edge sells units in it, and `batchable` (the good is portable and in the year arrays). `offered`,
    `has_units` and `funded` per market: some offer row, some offer with units, some bid with a budget."""
    bid_rows = _rows_of_good(bids.good, bids.row_count[0], good_id)
    offer_rows = _rows_of_good(offers.good, offers.row_count[0], good_id)
    bid_markets, offer_markets = bids.market[bid_rows], offers.market[offer_rows]
    distinct = numpy.unique(numpy.concatenate((bid_markets, offer_markets)))
    count = len(distinct)
    by_area = numpy.argsort(area_rank[market_area[distinct]], kind="mergesort")
    place_of = numpy.empty(count, dtype=numpy.int64)
    for place in range(count):
        place_of[by_area[place]] = place
    bid_position = place_of[numpy.searchsorted(distinct, bid_markets)]
    offer_position = place_of[numpy.searchsorted(distinct, offer_markets)]
    bid_grouped, bid_ptr = _grouped(bid_rows, bid_position, count)
    offer_grouped, offer_ptr = _grouped(offer_rows, offer_position, count)
    offered = numpy.zeros(count, dtype=numpy.bool_)
    has_units = numpy.zeros(count, dtype=numpy.bool_)
    edge_units = numpy.zeros(count, dtype=numpy.bool_)
    funded = numpy.zeros(count, dtype=numpy.bool_)
    for place in range(len(offer_rows)):
        row = offer_rows[place]
        market = offer_position[place]
        offered[market] = True
        if offers.quantity[row] > 0.0:
            has_units[market] = True
            if is_edge[offers.seller[row]] != 0:
                edge_units[market] = True
    for place in range(len(bid_rows)):
        if bids.budget[bid_rows[place]] > 0.0:
            funded[bid_position[place]] = True
    flags = has_units & ~edge_units & batchable
    return (distinct[by_area], bid_rows, bid_position, offer_rows, offer_position, bid_grouped, bid_ptr, offer_grouped, offer_ptr,
            flags, offered, has_units, funded)
