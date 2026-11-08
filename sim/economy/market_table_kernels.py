"""Whole-table reads and writes of the market memory's tables (`market_table_specs.py`).

Writers keep the two things a store's mapping depends on: a market entering a store takes the store's next entry number
(`next_order[store]`) and is counted (`member_count[store]`); a market leaving is uncounted. Readers take the table and return
arrays by market row. Rows are numbers in the `MarketTables` IdTables; a row of -1 means "no such market"."""
import numpy

from sim.compiled_tables.causes import Causes
from sim.jit import njit

from .market_table_specs import (CLEARED_PRICES, HELD_QUOTE_KIND, HELD_TRADE_AGE, HELD_YEARS_WITHOUT_BIDS,
                                 HELD_YEARS_WITHOUT_OFFERS, PRICES, QUOTE_KINDS, TRADE_AGE, USUAL_PRICES, VOLUME_WEIGHTS,
                                 YEARS_WITHOUT_BIDS, YEARS_WITHOUT_OFFERS)

CAUSES = Causes(("nan_value",))
NAN_VALUE = CAUSES.code("nan_value")

KIND_OFFERED, KIND_BARE, KIND_OTHER = 1, 2, 4      # bits of a quote kind's class (see year_arrays_memory)


@njit
def enter_store(order, next_order, member_count, store, row):
    """Give the market in `row` the next entry number of the store and count it as a member."""
    order[row] = next_order[store]
    next_order[store] += 1
    member_count[store] += 1


@njit
def put_floats(values, order, next_order, member_count, store, rows, new_values):
    """Set the store's figure for each market in `rows` (in this order); a market not yet in the store enters it.
    Returns 0, or NAN_VALUE at the first NaN figure (the rows before it are written): NaN is how the column says "none"."""
    for position in range(len(rows)):
        if numpy.isnan(new_values[position]):
            return NAN_VALUE
        row = rows[position]
        if numpy.isnan(values[row]):
            enter_store(order, next_order, member_count, store, row)
        values[row] = new_values[position]
    return 0


@njit
def drop_floats(values, member_count, store, rows):
    """Take each market in `rows` out of the store (a market not in it stays out)."""
    for position in range(len(rows)):
        row = rows[position]
        if not numpy.isnan(values[row]):
            values[row] = numpy.nan
            member_count[store] -= 1


@njit
def put_counts(values, held, order, next_order, member_count, store, bit, rows, new_values):
    """Set a whole-number store's figure (held under `bit`) for each market in `rows`, entering those not yet in it."""
    for position in range(len(rows)):
        row = rows[position]
        if held[row] & bit == 0:
            held[row] |= bit
            enter_store(order, next_order, member_count, store, row)
        values[row] = new_values[position]


@njit
def drop_counts(held, member_count, store, bit, rows):
    """Take each market in `rows` out of a whole-number store (held under `bit`)."""
    for position in range(len(rows)):
        row = rows[position]
        if held[row] & bit != 0:
            held[row] &= ~bit
            member_count[store] -= 1


@njit
def note_year_traded(markets, traded_rows, next_order, member_count):
    """A year ends: every market with a trade age is a year older, then each market in `traded_rows` (in this order) has age 0,
    entering the trade age store if it was not in it."""
    held, trade_age, order = markets.held, markets.trade_age, markets.order_trade_age     # columns read once: a helper that took the whole table would copy and count all of them on every call
    for row in range(markets.row_count[0]):
        if held[row] & HELD_TRADE_AGE != 0:
            trade_age[row] += 1
    for position in range(len(traded_rows)):
        row = traded_rows[position]
        if held[row] & HELD_TRADE_AGE == 0:
            held[row] |= HELD_TRADE_AGE
            enter_store(order, next_order, member_count, TRADE_AGE, row)
        trade_age[row] = 0


@njit
def markets_traded_within(markets, years):
    """Per market row: whether it cleared at most `years` years ago (a market with no trade age never did)."""
    held, trade_age = markets.held, markets.trade_age
    traded = numpy.zeros(markets.row_count[0], dtype=numpy.bool_)
    for row in range(markets.row_count[0]):
        traded[row] = held[row] & HELD_TRADE_AGE != 0 and trade_age[row] <= years
    return traded


@njit
def kind_class(held, quote_kind, class_of_kind):
    """The KIND_* bits of a market's quote kind: 0 when it has none."""
    if held & HELD_QUOTE_KIND == 0:
        return 0
    return class_of_kind[quote_kind]


@njit
def traded_last_year(held, trade_age):
    """Whether the market cleared last year (its trade age is 0)."""
    return held & HELD_TRADE_AGE != 0 and trade_age <= 0


@njit
def offered_prices(markets, class_of_kind):
    """Per market row: the price a buyer can buy at (`MarketMemory.offered_price`), NaN where none. A market that traded last year
    offers its price; otherwise a quote kind decides (class_of_kind[kind] has KIND_OFFERED), and a price with no kind is the
    opening's estimate, on offer only until the market has ever cleared."""
    price, held, trade_age, quote_kind = markets.price, markets.held, markets.trade_age, markets.quote_kind
    offered = numpy.full(markets.row_count[0], numpy.nan)
    for row in range(markets.row_count[0]):
        if numpy.isnan(price[row]):
            continue
        classes = kind_class(held[row], quote_kind[row], class_of_kind)
        if traded_last_year(held[row], trade_age[row]):
            offered[row] = price[row]
        elif classes == 0 and held[row] & HELD_TRADE_AGE == 0:
            offered[row] = price[row]
        elif classes & KIND_OFFERED != 0:
            offered[row] = price[row]
    return offered


@njit
def bare_quotes(markets, class_of_kind):
    """Per market row: whether the remembered price is a bid ceiling or an ask (a KIND_BARE kind) of a market that did not trade last year."""
    price, held, trade_age, quote_kind = markets.price, markets.held, markets.trade_age, markets.quote_kind
    bare = numpy.zeros(markets.row_count[0], dtype=numpy.bool_)
    for row in range(markets.row_count[0]):
        if not numpy.isnan(price[row]) and not traded_last_year(held[row], trade_age[row]):
            bare[row] = kind_class(held[row], quote_kind[row], class_of_kind) & KIND_BARE != 0
    return bare


@njit
def scatter_values(grid, values, good_rows, area_columns, count):
    """grid[good_rows[r], area_columns[r]] = values[r] for each market row r below `count` that has a figure (not NaN) and a cell
    (both indices of 0 or more)."""
    for row in range(count):
        if good_rows[row] >= 0 and area_columns[row] >= 0 and not numpy.isnan(values[row]):
            grid[good_rows[row], area_columns[row]] = values[row]


@njit
def scatter_flags(grid, flags, good_rows, area_columns, count):
    """grid[good_rows[r], area_columns[r]] = True for each market row r below `count` whose flag is set and that has a cell."""
    for row in range(count):
        if flags[row] and good_rows[row] >= 0 and area_columns[row] >= 0:
            grid[good_rows[row], area_columns[row]] = True


@njit
def market_of_good_tile(area_of_good_tile, market_of_good_area):
    """Per (good row, tile row): the goods market row of the good's area on that tile, -1 where the good has no market there
    or the memory has not numbered it (area_of_good_tile holds area columns, -1 for none)."""
    markets = numpy.full(area_of_good_tile.shape, -1, dtype=numpy.int64)
    for good in range(area_of_good_tile.shape[0]):
        for tile in range(area_of_good_tile.shape[1]):
            area = area_of_good_tile[good, tile]
            if area >= 0:
                markets[good, tile] = market_of_good_area[good, area]
    return markets


@njit
def carry_floats(old_values, old_order, new_values, new_order, old_to_new, old_count, new_rows, old_rows, next_order, member_count, store):
    """Float store across a redraw: markets that keep a row keep their entry number; each pair (new_rows[p] takes old_rows[p])
    then copies the old figure, entering the new market after those already there unless it is in the store already (it is
    overwritten in place)."""
    count = 0
    for old_row in range(old_count):
        new_row = old_to_new[old_row]
        if new_row >= 0 and not numpy.isnan(old_values[old_row]):
            new_values[new_row] = old_values[old_row]
            new_order[new_row] = old_order[old_row]
            count += 1
    for pair in range(len(new_rows)):
        old_row = old_rows[pair]
        if old_row < 0 or numpy.isnan(old_values[old_row]):
            continue
        new_row = new_rows[pair]
        if numpy.isnan(new_values[new_row]):
            new_order[new_row] = next_order[store]
            next_order[store] += 1
            count += 1
        new_values[new_row] = old_values[old_row]
    member_count[store] = count


@njit
def carry_counts(old_values, old_held, old_order, new_values, new_held, new_order, bit, old_to_new, old_count, new_rows, old_rows,
                 next_order, member_count, store):
    """`carry_floats` for a whole-number store held under `bit`."""
    count = 0
    for old_row in range(old_count):
        new_row = old_to_new[old_row]
        if new_row >= 0 and old_held[old_row] & bit != 0:
            new_values[new_row] = old_values[old_row]
            new_held[new_row] |= bit
            new_order[new_row] = old_order[old_row]
            count += 1
    for pair in range(len(new_rows)):
        old_row = old_rows[pair]
        if old_row < 0 or old_held[old_row] & bit == 0:
            continue
        new_row = new_rows[pair]
        if new_held[new_row] & bit == 0:
            new_held[new_row] |= bit
            new_order[new_row] = next_order[store]
            next_order[store] += 1
            count += 1
        new_values[new_row] = old_values[old_row]
    member_count[store] = count


@njit
def remap_goods_markets(old, new, old_to_new, new_rows, old_rows, next_order, member_count):
    """Fill `new` (rows numbered, `first`/`area` set, floats NaN, `held` 0) from `old` after the areas are redrawn: `old_to_new[r]`
    is the new row of old market r that survives (-1: dropped); pair p says new market `new_rows[p]` takes the figures of old
    market `old_rows[p]` (-1: the old one was never numbered). Pairs are applied in order, after the survivors."""
    count = old.row_count[0]
    carry_floats(old.price, old.order_price, new.price, new.order_price, old_to_new, count, new_rows, old_rows,
                 next_order, member_count, PRICES)
    carry_floats(old.usual_price, old.order_usual_price, new.usual_price, new.order_usual_price, old_to_new, count, new_rows,
                 old_rows, next_order, member_count, USUAL_PRICES)
    carry_floats(old.cleared_price, old.order_cleared_price, new.cleared_price, new.order_cleared_price, old_to_new, count,
                 new_rows, old_rows, next_order, member_count, CLEARED_PRICES)
    carry_floats(old.volume_weight, old.order_volume_weight, new.volume_weight, new.order_volume_weight, old_to_new, count,
                 new_rows, old_rows, next_order, member_count, VOLUME_WEIGHTS)
    carry_counts(old.trade_age, old.held, old.order_trade_age, new.trade_age, new.held, new.order_trade_age, HELD_TRADE_AGE,
                 old_to_new, count, new_rows, old_rows, next_order, member_count, TRADE_AGE)
    carry_counts(old.years_without_bids, old.held, old.order_years_without_bids, new.years_without_bids, new.held,
                 new.order_years_without_bids, HELD_YEARS_WITHOUT_BIDS, old_to_new, count, new_rows, old_rows, next_order,
                 member_count, YEARS_WITHOUT_BIDS)
    carry_counts(old.years_without_offers, old.held, old.order_years_without_offers, new.years_without_offers, new.held,
                 new.order_years_without_offers, HELD_YEARS_WITHOUT_OFFERS, old_to_new, count, new_rows, old_rows, next_order,
                 member_count, YEARS_WITHOUT_OFFERS)
    carry_counts(old.quote_kind, old.held, old.order_quote_kind, new.quote_kind, new.held, new.order_quote_kind, HELD_QUOTE_KIND,
                 old_to_new, count, new_rows, old_rows, next_order, member_count, QUOTE_KINDS)
