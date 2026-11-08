"""The memory's count of years a market lacked bids or offers, for all the markets of a good in one kernel call.

`goods_good_clear.note_idle_years` did this market by market through the memory's wrappers (`count_year_without_bids`,
`end_years_without_bids`, `count_year_without_offers`, `end_years_without_offers`); `note_idle_years` does it on the goods table's
columns. A market that has offers and no funded bid counts a year without bids (and enters that store when new); otherwise the
count ends and the market leaves the store. The same for bids and no units on offer. The answer per market is the two counts
before this year, added."""
import numpy

from sim.jit import njit

from .market_table_specs import HELD_YEARS_WITHOUT_BIDS, HELD_YEARS_WITHOUT_OFFERS, YEARS_WITHOUT_BIDS, YEARS_WITHOUT_OFFERS


@njit
def count_or_end(values, held, order, next_order, member_count, store, bit, row, counting):
    """One store's step for a market: with `counting` its count rises by one (entering the store when new), else the count ends
    (the market leaves the store). Returns the count before."""
    here = held[row] & bit != 0
    before = values[row] if here else 0
    if counting:
        if not here:
            held[row] |= bit
            order[row] = next_order[store]
            next_order[store] += 1
            member_count[store] += 1
        values[row] = before + 1
    elif here:
        held[row] &= ~bit
        member_count[store] -= 1
    return before


@njit
def note_idle_years(years_without_bids, years_without_offers, held, order_bids, order_offers, next_order, member_count, rows,
                    has_offers, has_units, has_funded_bid):
    """The counts of years without bids and without offers for each market in `rows`, in this order, from what the market had this
    year: any offer row (`has_offers`), any offer with units (`has_units`), any bid with a budget (`has_funded_bid`). Returns per
    market the two counts before this year, added."""
    before = numpy.zeros(len(rows), dtype=numpy.int64)
    for place in range(len(rows)):
        row = rows[place]
        without_bids = count_or_end(years_without_bids, held, order_bids, next_order, member_count, YEARS_WITHOUT_BIDS,
                                    HELD_YEARS_WITHOUT_BIDS, row, has_offers[place] and not has_funded_bid[place])
        without_offers = count_or_end(years_without_offers, held, order_offers, next_order, member_count, YEARS_WITHOUT_OFFERS,
                                      HELD_YEARS_WITHOUT_OFFERS, row, (not has_units[place]) and has_funded_bid[place])
        before[place] = without_bids + without_offers
    return before
