"""A good's cleared markets as the columns `goods_good_clear.GoodClearing` keeps, in one kernel call: how each market was cleared,
its first round's figures (from the batch where it traded, from the untraded quote figures where it did not), the quote, and the
offers that keep units after the first round market by market (`GoodClearing.__init__` and `_count_left` made about sixty numpy
calls per good for these).

A market is `TABLE_TRADED` (the batch traded in it), `TABLE_UNTRADED` (batched without trading, or no offer with units: its quote
is read from the columns) or `ON_OBJECTS` (anything else; the caller clears it on `Bid` and `Offer` objects and fills in its figures)."""
import numpy

from sim.jit import njit

TABLE_TRADED, TABLE_UNTRADED, ON_OBJECTS = 0, 1, 2
NO_QUOTE, BID_QUOTE, ASK_QUOTE = 0, 1, 2


@njit
def clearing_columns(flags, has_units, last_price, batch_traded, batch_mean, batch_quantity, batch_requested, batch_supply, batch_left,
                     batch_offer_ptr, batch_offer_rows, lowest_ask, lowest_clamped, untraded_supply, untraded_wanted, best_bid, funded,
                     offer_grouped, offer_ptr, offer_quantity):
    """(slots, way, quantity, price, demand, offered, wanted, quote_price, quote_kind, left_grouped, left_ptr, left_count) of a
    good's markets (`flags` says which the batch cleared; `slots` is each one's place in the batch, -1 for the rest).

    The `batch_*` arrays are the batch's allocation (per batched market, and `batch_left` per offer of the batch, cut by
    `batch_offer_ptr`; empty when nothing was batched), the `untraded_*`, `lowest_*`, `best_bid` and `funded` arrays the quote figures
    per market of the good (empty when no market needs them). `offer_grouped` and `offer_ptr` cut the good's offer rows by market."""
    count = len(flags)
    slots = numpy.full(count, -1, dtype=numpy.int64)
    batched_markets = 0
    for place in range(count):
        if flags[place]:
            slots[place] = batched_markets
            batched_markets += 1
    way = numpy.empty(count, dtype=numpy.int64)
    quantity = numpy.zeros(count)
    price = numpy.full(count, numpy.nan)
    demand = numpy.zeros(count)
    offered = numpy.zeros(count)
    wanted = numpy.zeros(count)
    quote_price = numpy.full(count, numpy.nan)
    quote_kind = numpy.zeros(count, dtype=numpy.int64)
    place_of_slot = numpy.full(batched_markets, -1, dtype=numpy.int64)
    left_count = numpy.zeros(count, dtype=numpy.int64)
    for place in range(count):
        slot = slots[place]
        if slot >= 0 and batch_traded[slot]:
            way[place] = TABLE_TRADED
            place_of_slot[slot] = place
            price[place], quantity[place] = batch_mean[slot], batch_quantity[slot]
            demand[place], offered[place] = batch_requested[slot], batch_supply[slot]
            wanted[place] = demand[place]
        elif slot >= 0 or not has_units[place]:
            way[place] = TABLE_UNTRADED
            asked, clamped, previous = lowest_ask[place], lowest_clamped[place], last_price[place]
            keeps_last = numpy.isnan(clamped) or (not numpy.isnan(previous) and clamped <= previous)
            price[place] = previous if keeps_last else clamped
            offered[place], wanted[place] = untraded_supply[place], untraded_wanted[place]
            bid_quote = not numpy.isnan(best_bid[place]) and (numpy.isnan(asked) or best_bid[place] < asked)
            ask_quote = not bid_quote and not numpy.isnan(asked) and not funded[place]
            if bid_quote:
                quote_price[place], quote_kind[place] = best_bid[place], BID_QUOTE
            elif ask_quote:
                quote_price[place], quote_kind[place] = asked, ASK_QUOTE
            for each in range(offer_ptr[place], offer_ptr[place + 1]):
                if offer_quantity[offer_grouped[each]] > 0.0:
                    left_count[place] += 1
        else:
            way[place] = ON_OBJECTS
    for slot in range(batched_markets):
        place = place_of_slot[slot]
        if place >= 0:
            for offer in range(batch_offer_ptr[slot], batch_offer_ptr[slot + 1]):
                if batch_left[offer] > 0.0:
                    left_count[place] += 1
    left_ptr = numpy.zeros(count + 1, dtype=numpy.int64)
    for place in range(count):
        left_ptr[place + 1] = left_ptr[place] + left_count[place]
    left_grouped = numpy.empty(left_ptr[count], dtype=numpy.int64)
    for place in range(count):
        found = left_ptr[place]
        if way[place] == TABLE_TRADED:
            slot = slots[place]
            for offer in range(batch_offer_ptr[slot], batch_offer_ptr[slot + 1]):
                if batch_left[offer] > 0.0:
                    left_grouped[found] = batch_offer_rows[offer]
                    found += 1
        elif way[place] == TABLE_UNTRADED:
            for each in range(offer_ptr[place], offer_ptr[place + 1]):
                if offer_quantity[offer_grouped[each]] > 0.0:
                    left_grouped[found] = offer_grouped[each]
                    found += 1
    return slots, way, quantity, price, demand, offered, wanted, quote_price, quote_kind, left_grouped, left_ptr, left_count
