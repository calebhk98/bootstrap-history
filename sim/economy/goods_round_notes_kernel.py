"""A good's cleared first rounds noted in the ledger, and the markets whose fills the ledger may keep, in one kernel call
(`goods_settle.note_clearings`).

The rounds are `year_ledger_note_kernels.add_rounds` over all the good's markets in clearing order. The markets with fills to keep are those
on the objects, and those that traded in the batch: all of them when no watcher is set, none when the watchers bought nothing, else those
in which a watcher's bid took units (`watched`, per bid of the batch, summed over each market's bid rows)."""
import numpy

from sim.economy.goods_clearing_kernel import ON_OBJECTS, TABLE_TRADED
from sim.economy.year_ledger_note_kernels import add_rounds
from sim.jit import njit

ALL_TRADED, NO_TRADED, WATCHED_TRADED = range(3)       # which of the markets that traded in the batch keep fills


@njit
def markets_with_fills(way, slots, bid_ptr, watched, which):
    """The markets (in clearing order) whose fills the ledger may keep. `bid_ptr` cuts the batch's bids by market `slots[place]`."""
    keep = numpy.zeros(len(way), dtype=numpy.bool_)
    count = 0
    for place in range(len(way)):
        if way[place] == ON_OBJECTS:
            keep[place] = True
        elif way[place] == TABLE_TRADED:
            if which == ALL_TRADED:
                keep[place] = True
            elif which == WATCHED_TRADED:
                for bid in range(bid_ptr[slots[place]], bid_ptr[slots[place] + 1]):
                    keep[place] = keep[place] or watched[bid]
        if keep[place]:
            count += 1
    places = numpy.zeros(count, dtype=numpy.int64)
    at = 0
    for place in range(len(way)):
        if keep[place]:
            places[at] = place
            at += 1
    return places


@njit
def note_good_rounds(way, slots, bid_ptr, watched, which, rounds, delivered, order_delivered, market_counters, markets, quantity, price,
                     moved):
    """Note the good's rounds (the caller has reserved a row for each) and answer the markets with fills to keep."""
    add_rounds(rounds, delivered, order_delivered, market_counters, markets, quantity, price, moved)
    return markets_with_fills(way, slots, bid_ptr, watched, which)
