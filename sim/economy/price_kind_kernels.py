"""The kind of each good's remembered price, worked out over the goods market table's columns in one pass.

`MarketMemory.price_kind` says what one market's price is; `kinds_by_good` says it for a good across its markets, as the
loop over the sorted market keys did: traded when any market of the good traded last year, else the kind of the good's
first priced market in market-name order."""
import numpy

from sim.jit import njit

from .market_table_specs import HELD_QUOTE_KIND, HELD_TRADE_AGE, KEY_SEPARATOR

NO_KIND, SMOOTHED_TRADE, REMEMBERED, OPENING_ESTIMATE = -1, -2, -3, -4       # the codes of `kinds_by_good` below a quote kind's number


@njit
def kinds_by_good(markets, area_rank, good_count):
    """Per good number: the code of its price's kind, NO_KIND when no market of it holds a price. SMOOTHED_TRADE when some priced
    market traded last year (trade age 0); otherwise the kind of the priced market whose area has the lowest `area_rank` (the
    place of its name among the area names in sorted order): REMEMBERED (it traded in an earlier year), a quote kind's number, or
    OPENING_ESTIMATE (no clearing and no quote). `area_rank` is indexed by area number; `good_count` is the goods numbering's size."""
    price, held, trade_age, quote_kind = markets.price, markets.held, markets.trade_age, markets.quote_kind
    first, area = markets.first, markets.area
    codes = numpy.full(good_count, NO_KIND, dtype=numpy.int64)
    best_rank = numpy.full(good_count, -1, dtype=numpy.int64)
    for row in range(markets.row_count[0]):
        if numpy.isnan(price[row]):
            continue
        good = first[row]
        if held[row] & HELD_TRADE_AGE != 0 and trade_age[row] <= 0:
            codes[good] = SMOOTHED_TRADE
            best_rank[good] = -2           # nothing replaces a traded kind
            continue
        if best_rank[good] == -2:
            continue
        rank = area_rank[area[row]]
        if best_rank[good] != -1 and best_rank[good] <= rank:
            continue
        best_rank[good] = rank
        if held[row] & HELD_QUOTE_KIND != 0:
            codes[good] = quote_kind[row]
        elif held[row] & HELD_TRADE_AGE != 0:
            codes[good] = REMEMBERED
        else:
            codes[good] = OPENING_ESTIMATE
    return codes


def price_kinds_of_goods(tables, smoothed_name: str, remembered_name: str, opening_name: str) -> dict:
    """{good: kind name} for every good with a priced market, goods in the order of their first priced market's name (the order a
    sort of the market names lists them), from `kinds_by_good` over the goods table of `tables` (`MarketTables`)."""
    area_names = tables.areas.name_list
    area_rank = numpy.empty(len(area_names), dtype=numpy.int64)
    area_rank[sorted(range(len(area_names)), key=area_names.__getitem__)] = numpy.arange(len(area_names))
    good_names, kind_names = tables.goods.name_list, tables.kinds.name_list
    codes = kinds_by_good(tables.goods_table, area_rank, len(good_names))
    named = {SMOOTHED_TRADE: smoothed_name, REMEMBERED: remembered_name, OPENING_ESTIMATE: opening_name}
    present = numpy.flatnonzero(codes != NO_KIND).tolist()
    # a good's markets all start with its name and a separator, so goods order by that prefix, whatever the areas are
    present.sort(key=lambda number: good_names[number] + KEY_SEPARATOR)
    return {good_names[number]: named[code] if code < 0 else kind_names[code]
            for number, code in zip(present, codes[present].tolist())}
