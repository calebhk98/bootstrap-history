"""Kernels over the merchant table (merchant_table.py) for the year's close: the news merchants hear, what they hold, the profit
they settle and the hauls on the road. Each takes arrays and returns arrays; `merchant_year.py` is the boundary that builds them.

Sums that Python took with `math.fsum` are `exact_sum`, so a merchant's stock value is the number the dictionary loop gave."""
import numpy

from sim.jit import njit
from sim.labour.market.exact_sums import exact_sum

NOT_HEARD = -(10 ** 9)          # merchants_news.NOT_HEARD: the lag of a market whose area is gone
HISTORY_STRIDE = 1 << 32        # merchant_table.HISTORY_STRIDE


@njit
def find_key(keys, key):
    """The position of `key` in the sorted `keys`, or -1."""
    low, high = 0, len(keys)
    while low < high:
        middle = (low + high) // 2
        if keys[middle] < key:
            low = middle + 1
        else:
            high = middle
    if low < len(keys) and keys[low] == key:
        return low
    return -1


@njit
def hear_all(rows, price_rows, price_values, lags, history_key, history_starts, history_price):
    """What every merchant hears of the year's prices, and its price history after the year.

    `rows` (merchants) and `price_rows` (goods markets) number the cells; `lags[k, p]` is the years of news between merchant k and
    market p. A lag of zero or less hears the price at once (`NOT_HEARD` or below hears nothing); a longer lag appends the price to the
    cell's history, keeps the last `lag + 1`, and hears the oldest once the history is longer than the lag. Returns (heard price per
    cell, whether the cell is heard, the new history keys, starts and prices): the histories of cells with no lag this year are kept."""
    merchants, markets = len(rows), len(price_rows)
    heard = numpy.empty((merchants, markets))
    kept = numpy.zeros((merchants, markets), numpy.bool_)
    touched_key = numpy.empty(merchants * markets, numpy.int64)
    touched_cell = numpy.empty(merchants * markets, numpy.int64)
    touched = 0
    for merchant in range(merchants):
        for market in range(markets):
            lag = lags[merchant, market]
            heard[merchant, market] = price_values[market]
            kept[merchant, market] = lag > NOT_HEARD
            if lag > 0:
                touched_key[touched] = rows[merchant] * HISTORY_STRIDE + price_rows[market]
                touched_cell[touched] = merchant * markets + market
                touched += 1
    order = numpy.argsort(touched_key[:touched])
    lengths = numpy.empty(touched, numpy.int64)
    old_at = numpy.empty(touched, numpy.int64)
    gone = 0                                   # old values that a touched history replaces
    for place in range(touched):
        cell = touched_cell[order[place]]
        lag = lags[cell // markets, cell % markets]
        found = find_key(history_key, touched_key[order[place]])
        old_at[place] = found
        old_length = 0 if found < 0 else history_starts[found + 1] - history_starts[found]
        lengths[place] = min(old_length + 1, lag + 1)
        gone += old_length
    total = len(history_price) - gone
    for place in range(touched):
        total += lengths[place]
    new_key = numpy.empty(len(history_key) + touched, numpy.int64)
    new_starts = numpy.zeros(len(history_key) + touched + 1, numpy.int64)
    new_price = numpy.empty(total)
    count = 0
    written = 0
    old_place = 0
    for place in range(touched + 1):
        limit = numpy.iinfo(numpy.int64).max if place == touched else touched_key[order[place]]
        while old_place < len(history_key) and history_key[old_place] < limit:      # histories this year leaves as they are
            new_key[count] = history_key[old_place]
            for item in range(history_starts[old_place], history_starts[old_place + 1]):
                new_price[written] = history_price[item]
                written += 1
            count += 1
            new_starts[count] = written
            old_place += 1
        if place == touched:
            break
        if old_place < len(history_key) and history_key[old_place] == limit:      # the old history of a touched cell is replaced
            old_place += 1
        cell = touched_cell[order[place]]
        merchant, market = cell // markets, cell % markets
        lag = lags[merchant, market]
        found = old_at[place]
        old_length = 0 if found < 0 else history_starts[found + 1] - history_starts[found]
        keep_length = lengths[place]
        first = old_length + 1 - keep_length            # items of (old history + the new price) that fall off the front
        new_key[count] = touched_key[order[place]]
        for item in range(keep_length):
            position = first + item
            if position < old_length:
                new_price[written] = history_price[history_starts[found] + position]
            else:
                new_price[written] = price_values[market]
            written += 1
        if keep_length > lag:
            heard[merchant, market] = new_price[written - keep_length]
        else:
            kept[merchant, market] = False
        count += 1
        new_starts[count] = written
    return heard, kept, new_key[:count], new_starts[:count + 1], new_price[:written]


@njit
def merchant_stock(first_slots, next_in_agent, stock_good, stock_tile, stock_quantity):
    """The positive stock rows of the merchants whose first book stock slot is `first_slots[k]` (-1: holds nothing).
    Returns (merchant position k, good number, tile number, quantity) per row, merchants in order, rows in the order the book made them."""
    count = 0
    for merchant in range(len(first_slots)):
        slot = first_slots[merchant]
        while slot != -1:
            if stock_quantity[slot] > 0.0:
                count += 1
            slot = next_in_agent[slot]
    owner = numpy.empty(count, numpy.int64)
    good = numpy.empty(count, numpy.int64)
    tile = numpy.empty(count, numpy.int64)
    quantity = numpy.empty(count)
    position = 0
    for merchant in range(len(first_slots)):
        slot = first_slots[merchant]
        while slot != -1:
            if stock_quantity[slot] > 0.0:
                owner[position], good[position] = merchant, stock_good[slot]
                tile[position], quantity[position] = stock_tile[slot], stock_quantity[slot]
                position += 1
            slot = next_in_agent[slot]
    return owner, good, tile, quantity


@njit
def settle_profits(rows, cash, capital_base, prices, owner_k, market_row, quantity, interest_rate, payout_share):
    """Each merchant's year-end settlement (`merchants.close_year` after the learning): wealth is cash plus its stock (held and on the road)
    valued at its expected prices, the stock with no learned price left out; profit is wealth above `capital_base`.

    A loss shrinks the capital to the wealth unless some stock was unpriced. A profit that beats `interest_rate` on the capital pays out
    `payout_share` of it and the rest becomes capital; otherwise the owner takes it all. `owner_k`, `market_row` (-1: a market with no
    number) and `quantity` are the stock rows, grouped by merchant position k in order. Writes `capital_base[rows[k]]`; returns the
    payout per merchant (0.0: none)."""
    payout = numpy.zeros(len(rows))
    values = numpy.empty(len(quantity))
    place = 0
    for merchant in range(len(rows)):
        count = 0
        unpriced = False
        while place < len(owner_k) and owner_k[place] == merchant:
            price = numpy.nan if market_row[place] < 0 else prices[rows[merchant], market_row[place]]
            if price != price:
                unpriced = True
            else:
                values[count] = quantity[place] * price
                count += 1
            place += 1
        wealth = cash[merchant] + exact_sum(values, count)
        base = capital_base[rows[merchant]]
        profit = wealth - base
        if profit <= 0.0:
            if not unpriced:
                capital_base[rows[merchant]] = max(0.0, wealth)
            continue
        earns_more = base > 0.0 and profit / base > interest_rate
        share = payout_share if earns_more else 1.0
        taken = min(max(0.0, cash[merchant]), share * profit)
        if earns_more:
            capital_base[rows[merchant]] = wealth - taken
        if taken > 0.0:
            payout[merchant] = taken
    return payout
