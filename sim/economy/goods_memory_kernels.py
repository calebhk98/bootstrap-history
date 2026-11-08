"""The market memory's notes after a year of clearing, over every goods market of the year in one kernel call each.

`year_goods._remember_markets` worked out each market's signal and then wrote the memory market by market (`set_quote_kind`,
`drop_quote_kind`, `set_price`, `note_usual_price`, `note_cleared`) in sorted (good, area) order; `note_markets` does those
writes for all of them on the memory's goods table columns, in the same order and with the same entry numbers: a market enters
a store (takes `next_order[store]`, is counted) the first time it is written to that store, and each store's order depends only
on the markets written to it, so one loop over the markets gives what the five wrapper calls gave. `note_volumes` is
`MarketMemory.note_volume` over the year's markets and `decay_unseen_volumes` its decay for the markets that had no orders.

Every column of the memory table is documented in `market_table_specs.py`; a figure a market does not hold is NaN there."""
import numpy

from sim.jit import njit

from .market_table_specs import HELD_QUOTE_KIND, PRICES, QUOTE_KINDS, USUAL_PRICES, CLEARED_PRICES, VOLUME_WEIGHTS

NO_KIND = -1      # `new_kind` of a market whose quote kind is not set


@njit
def enter_float_store(order, next_order, member_count, store, row):
    """The market in `row` enters a float store: the next entry number, counted."""
    order[row] = next_order[store]
    next_order[store] += 1
    member_count[store] += 1


@njit
def drop_kind(held, member_count, row):
    """The market in `row` loses its quote kind (a market with none stays as it is)."""
    if held[row] & HELD_QUOTE_KIND != 0:
        held[row] &= ~HELD_QUOTE_KIND
        member_count[QUOTE_KINDS] -= 1


@njit
def remembered_price_after(signal, opening, floor_share):
    """The price a market remembers for a positive `signal`: the signal, but no less than `floor_share` of the good's opening
    price (of the signal itself where the good has none: `opening` is NaN)."""
    base = signal if numpy.isnan(opening) else opening
    floor = base * floor_share
    return floor if floor > signal else signal


@njit
def note_markets(price, usual_price, cleared_price, held, quote_kind, order_price, order_usual_price, order_cleared_price,
                 order_quote_kind, next_order, member_count, rows, signal, new_kind, from_trade, round_price, delivered, opening,
                 floor_share, usual_speed):
    """For each market in `rows`, in this order, what `_remember_markets` wrote after its clearings:
    a market whose price came from a trade (`from_trade`) first loses its quote kind; a `new_kind` (a number in the quote kind
    table, NO_KIND for none) is set; a `signal` above zero becomes the remembered price (`remembered_price_after`, `opening` being
    the good's opening price today or NaN) and moves the usual price toward it (`usual_speed`, starting at it when new); the
    cleared price is `round_price` when the market delivered goods and the price is above zero, else forgotten; a market that
    delivered goods loses its quote kind. Returns how many markets delivered goods."""
    traded = 0
    for place in range(len(rows)):
        row = rows[place]
        if from_trade[place]:
            drop_kind(held, member_count, row)
        if new_kind[place] != NO_KIND:
            if held[row] & HELD_QUOTE_KIND == 0:
                held[row] |= HELD_QUOTE_KIND
                order_quote_kind[row] = next_order[QUOTE_KINDS]
                next_order[QUOTE_KINDS] += 1
                member_count[QUOTE_KINDS] += 1
            quote_kind[row] = new_kind[place]
        if signal[place] > 0.0:
            value = remembered_price_after(signal[place], opening[place], floor_share)
            if numpy.isnan(price[row]):
                enter_float_store(order_price, next_order, member_count, PRICES, row)
            price[row] = value
            usual = usual_price[row]
            if numpy.isnan(usual):
                enter_float_store(order_usual_price, next_order, member_count, USUAL_PRICES, row)
                usual_price[row] = value
            else:
                usual_price[row] = usual + usual_speed * (value - usual)
        if delivered[place] > 0.0 and round_price[place] > 0.0:      # a NaN price is not above zero
            if numpy.isnan(cleared_price[row]):
                enter_float_store(order_cleared_price, next_order, member_count, CLEARED_PRICES, row)
            cleared_price[row] = round_price[place]
        elif not numpy.isnan(cleared_price[row]):
            cleared_price[row] = numpy.nan
            member_count[CLEARED_PRICES] -= 1
        if delivered[place] > 0.0:
            drop_kind(held, member_count, row)
            traded += 1
    return traded


@njit
def note_volumes(volume_weight, order_volume_weight, next_order, member_count, rows, quantity, speed):
    """`MarketMemory.note_volume` for each market in `rows`, in this order: the usual volume moves toward the quantity (starting at
    it when new, entering the store)."""
    for place in range(len(rows)):
        row = rows[place]
        old = volume_weight[row]
        if numpy.isnan(old):
            enter_float_store(order_volume_weight, next_order, member_count, VOLUME_WEIGHTS, row)
            volume_weight[row] = quantity[place]
        else:
            volume_weight[row] = old + speed * (quantity[place] - old)


@njit
def decay_unseen_volumes(volume_weight, count, seen, speed):
    """The usual volume of every market below `count` that holds one and is not flagged `seen` moves toward zero."""
    for row in range(count):
        if not seen[row] and not numpy.isnan(volume_weight[row]):
            volume_weight[row] = volume_weight[row] + speed * (0.0 - volume_weight[row])
