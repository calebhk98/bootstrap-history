"""What the market memory learns from a year's goods markets, over whole columns (`year_goods._remember_markets`): the price the sellers
got, what the market's own buyers would have taken at the remembered price, and the signal each market's memory moves toward.

The rules are those of `market_memory_asks`, `market_memory_offers`, `year_goods.price_after_trade`, `goods_market._quantity` and
`goods_market_rows.wanted_at_rows`, bit for bit: where the Python adds with `math.fsum` the kernels add with `exact_sum`, and a power the
Python raises on, or a quantity that is not finite, sets `flags[0]` (`FALLBACK`) and the caller runs the Python rules. NaN stands for
"none" in every column. The plain Python these replace is `sim/tests/remember_plain.py`."""
import numpy

from sim.jit import njit

from .year_ledger_note_kernels import exact_sum

KERNEL = {"error_model": "numpy"}
FALLBACK = 1                    # flags[0] once a figure left the range these kernels reproduce
NO_QUOTE, BEST_UNFILLED_BID, LOWEST_UNFILLED_ASK, COST_COVERING = 0, 1, 2, 3      # the codes of a quote's kind


@njit(**KERNEL)
def received_prices(round_market, round_quantity, round_price, round_count, market_count):
    """Per market number: the price its sellers got per unit over the year's rounds that matched something, weighted by quantity
    (`year_goods._received_price` for a market that is not the coin metal's); NaN where no round matched a unit."""
    firsts = numpy.full(market_count, -1, dtype=numpy.int64)
    counts = numpy.zeros(market_count, dtype=numpy.int64)
    for row in range(round_count):
        if round_quantity[row] > 0.0:
            counts[round_market[row]] += 1
    starts = numpy.zeros(market_count + 1, dtype=numpy.int64)
    for market in range(market_count):
        starts[market + 1] = starts[market] + counts[market]
    taken = starts[:-1].copy()
    units = numpy.empty(starts[market_count])
    money = numpy.empty(starts[market_count])
    for row in range(round_count):
        if round_quantity[row] > 0.0:
            market = round_market[row]
            units[taken[market]] = round_quantity[row]
            money[taken[market]] = round_quantity[row] * round_price[row]
            taken[market] += 1
    received = numpy.full(market_count, numpy.nan)
    for market in range(market_count):
        if counts[market] > 0:
            first, count = starts[market], counts[market]
            total = exact_sum(units[first:first + count], count)
            if total > 0.0:
                received[market] = exact_sum(money[first:first + count], count) / total
    return received


@njit(**KERNEL)
def one_quantity(floor, flexible, reference, elasticity, budget, price, flags):
    """`goods_market._quantity` of one schedule at a positive price; a power the Python raises on, or a figure that is not finite, flags the fallback."""
    wanted = floor
    if flexible > 0.0 and reference > 0.0:
        base = price / reference
        if base == 0.0 and elasticity > 0.0:
            flags[0] = FALLBACK
        wanted += flexible * base ** -elasticity
    cap = budget / price
    answer = cap if cap < wanted else wanted
    if not numpy.isfinite(answer):
        flags[0] = FALLBACK
    return answer


@njit(**KERNEL)
def wanted_at_markets(price, bid_ptr, floor, flexible, reference, elasticity, budget, maximum, counted, added_ptr, added_flexible,
                      added_reference, added_elasticity, added_budget, added_maximum, flags):
    """Per market, what its own buyers would take at `price` (NaN or not above zero: none, so zero): the market's first-round bids
    (`bid_ptr` cuts the columns by market; `counted` is false for the foreign partner's, which is left out) and the bids later rounds added
    (`added_ptr`, a floor of zero), each as `goods_market.quantity_at`, added exactly."""
    markets = len(price)
    wanted = numpy.zeros(markets)
    for market in range(markets):
        at = price[market]
        if not at > 0.0:
            continue
        size = bid_ptr[market + 1] - bid_ptr[market] + added_ptr[market + 1] - added_ptr[market]
        pieces = numpy.zeros(size)
        used = 0
        for bid in range(bid_ptr[market], bid_ptr[market + 1]):
            if counted[bid]:
                if not (budget[bid] <= 0.0 or at > maximum[bid]):
                    pieces[used] = one_quantity(floor[bid], flexible[bid], reference[bid], elasticity[bid], budget[bid], at, flags)
                used += 1
        for bid in range(added_ptr[market], added_ptr[market + 1]):
            if not (added_budget[bid] <= 0.0 or at > added_maximum[bid]):
                pieces[used] = one_quantity(0.0, added_flexible[bid], added_reference[bid], added_elasticity[bid], added_budget[bid], at, flags)
            used += 1
        wanted[market] = exact_sum(pieces, used)
    return wanted


@njit(**KERNEL)
def bid_figures(bid_ptr, budget, maximum):
    """Per market: whether some first-round bid has a budget, and the highest finite ceiling above zero among those (NaN: none)
    (`goods_market_rows.bids_only_quote`)."""
    markets = len(bid_ptr) - 1
    funded = numpy.zeros(markets, dtype=numpy.bool_)
    best = numpy.full(markets, numpy.nan)
    for market in range(markets):
        for bid in range(bid_ptr[market], bid_ptr[market + 1]):
            if budget[bid] > 0.0:
                funded[market] = True
                if numpy.isfinite(maximum[bid]) and maximum[bid] > 0.0 and not maximum[bid] <= best[market]:
                    best[market] = maximum[bid]
    return funded, best


@njit(**KERNEL)
def remembered(old, cleared, quantity, usual):
    """`year_goods.remembered_price`."""
    if numpy.isnan(old) or usual <= 0.0:
        return cleared
    share = quantity / usual
    return old + (share if share < 1.0 else 1.0) * (cleared - old)


@njit(**KERNEL)
def price_after_trade(old, old_was_quote, cleared, quantity, reference_volume, quiet_years, resumed_share):
    """`year_goods.price_after_trade` (the resumed-trade rule included)."""
    if old_was_quote and not numpy.isnan(old):
        return remembered(old, cleared, quantity, reference_volume)
    paid = numpy.nan if old_was_quote else old
    volume_rule = remembered(paid, cleared, quantity, reference_volume)
    if numpy.isnan(paid) or quiet_years <= 0:
        return volume_rule
    return paid + resumed_share * (volume_rule - paid)


@njit(**KERNEL)
def price_after_thin_trade(price, cost, quantity, usual, representative_share, thin_trade_share):
    """`market_memory_offers.price_after_thin_trade`."""
    if numpy.isnan(price) or numpy.isnan(cost) or cost <= 0.0 or cost >= price or usual <= 0.0:
        return price
    short = 1.0 - quantity / (representative_share * usual)
    return price + thin_trade_share * (short if short > 0.0 else 0.0) * (cost - price)


@njit(**KERNEL)
def signals(old, was_quote, usual, quiet_years, total, received, wanted_at_old, quote_price, quote_kind, has_bids, offers_left, cost,
            bid_funded, bid_best, representative_share, resumed_share, no_offer_share, thin_trade_share):
    """Per market: (the signal its memory moves toward (NaN: none), the kind of the quote it rests on (`NO_QUOTE` when it rests on trade or
    on nothing), whether it came from trade). A market that traded is weighed against its usual volume or a share of what buyers wanted
    at the old price; one that did not moves toward its quote, which for a market with bids and no offers left is what a maker would
    have to ask to cover its cost, else the best bid unfilled. A market with nothing to quote plans from the cost of making the good,
    taken whole (kind COST_COVERING); with no cost either its signal is NaN and the caller forgets its planning price."""
    markets = len(old)
    signal = numpy.full(markets, numpy.nan)
    kind = numpy.zeros(markets, dtype=numpy.int64)
    from_trade = numpy.zeros(markets, dtype=numpy.bool_)
    for market in range(markets):
        if total[market] > 0.0 and not numpy.isnan(received[market]):
            from_trade[market] = True
            wanted_share = representative_share * wanted_at_old[market]
            reference = wanted_share if wanted_share > usual[market] else usual[market]
            figure = price_after_trade(old[market], was_quote[market], received[market], total[market], reference, quiet_years[market],
                                       resumed_share)
            if total[market] < representative_share * usual[market]:
                figure = price_after_thin_trade(figure, cost[market], total[market], usual[market], representative_share, thin_trade_share)
            signal[market] = figure
            continue
        price, code = quote_price[market], quote_kind[market]
        if has_bids[market] and offers_left[market] == 0:
            if not numpy.isnan(cost[market]) and cost[market] > 0.0 and bid_funded[market]:
                price, code = cost[market], COST_COVERING
            elif not numpy.isnan(bid_best[market]):
                price, code = bid_best[market], BEST_UNFILLED_BID
            else:
                price, code = numpy.nan, NO_QUOTE
        if code == NO_QUOTE and not numpy.isnan(cost[market]) and cost[market] > 0.0:      # nothing traded and nothing to quote: plan from the making cost
            kind[market] = COST_COVERING
            signal[market] = cost[market]
            continue
        if code != NO_QUOTE:
            kind[market] = code
            signal[market] = price if numpy.isnan(old[market]) else old[market] + no_offer_share * (price - old[market])
    return signal, kind, from_trade
