"""The year's goods markets re-priced and searched in one kernel call: for every market with bids and offers, what
`seller_offers.strategic_offers` and `unsold_search.clear_with_search` do (the sellers' re-pricing, the unsold-stock search
down to the floors, the sold-out raise up to the band), over arrays and with the same rules in the same order. The kernel
returns each offer's final reservation; the caller clears the market once with them.

Offers are the ones with units to sell, in seller-and-tile order, markets one after another (`offer_ptr`); a market's bids
are its `Buyers` arrays (goods_market_kernels), concatenated (`bid_ptr`, tier starts in `tier_ptr`). Per offer: whether the seller
is a producer, its unit cost, the input share of a run's variable cost, the price it expects (NaN: none), whether it stands
for many workshops and how many, the units it expects to sell a year, the band multiple above cost, and the number of its
(seller, tile) within the market. Per market: the market size (NaN: no history), the lending rate of its area (NaN: none),
its good's spoilage, and the token minimum price."""
import numpy

from sim.book import ROUNDING_SHARE
from sim.jit import njit

from . import goods_market_kernels as kernels
from .price_setting_kernel import best_prices

KERNEL = {"error_model": "numpy"}
FLOOD_POINTS = 200            # unsold_search.flood_price's grid
FLOOD_TIE = 1e-9
UNSOLD_BOUND_MARGIN = 1e-12


@njit(**KERNEL)
def band_edge(cost, input_share, multiple):
    share = min(1.0, max(0.0, input_share))
    return cost * (share + multiple * (1.0 - share))


@njit(**KERNEL)
def queued_holding_value(reservation, stock, yearly_sales, rate, spoilage):
    """inventory.queued_holding_value."""
    if yearly_sales <= 0.0 or reservation <= 0.0:
        return 0.0
    surviving = 1.0 - min(1.0, max(0.0, spoilage))
    if surviving <= 0.0:
        return 0.0
    years_waited = max(0.0, stock / yearly_sales - 1.0)
    carried = surviving / (1.0 + max(rate, -0.99))
    return reservation * carried ** years_waited


@njit(**KERNEL)
def choose_asks(res0, qty, is_producer, cost, share, expected, workshops, crowd, expected_sales, multiple, size,
                intensity, grid_count, grid_start, grid_step, months, discount_rate):
    """seller_offers.strategic_offers: the reservations after each producer's opening ask, its crowd's expectation or its
    price search against the book as it stood."""
    count = len(res0)
    res = res0.copy()
    rival_counts = numpy.zeros(count)
    for i in range(count):
        if qty[i] > 0.0 and res0[i] > 0.0:
            rival_counts[i] = workshops[i]
    where = numpy.zeros(count, dtype=numpy.int64)
    values = numpy.zeros(count)
    ceilings = numpy.zeros(count)
    searching = 0
    for i in range(count):
        if not is_producer[i]:
            continue
        priced = cost[i]
        limit = band_edge(priced, share[i], multiple[i]) if numpy.isfinite(priced) else numpy.inf
        if res0[i] <= 0.0:
            if numpy.isfinite(priced) and priced > 0.0 and numpy.isfinite(expected[i]) and expected[i] > 0.0:
                res[i] = min(expected[i], limit)
                continue
        if crowd[i]:
            if numpy.isfinite(expected[i]) and expected_sales[i] > 0.0 and not qty[i] > expected_sales[i]:
                res[i] = max(res0[i], expected[i])
            continue
        value = min(priced, max(res0[i], 0.0))
        if res0[i] <= 0.0 or numpy.isnan(size):
            continue
        where[searching] = i
        values[searching] = value
        ceilings[searching] = max(limit, value)
        searching += 1
    if searching > 0:
        own = where[:searching].copy()
        chosen = best_prices(res0, rival_counts, own, res0[own], values[:searching].copy(), numpy.full(searching, size),
                             qty[own], values[:searching].copy(), ceilings[:searching].copy(), intensity, grid_count,
                             grid_start, grid_step, months, discount_rate)
        for j in range(searching):
            res[own[j]] = chosen[j]
    return res


@njit(**KERNEL)
def clear_figures(res, qty, minimum, has_minimum, floors, flexibles, budgets, references, exponents, maximums, capped,
                  tier_bounds):
    """(units each offer sells, the first round's requests in all, the units traded) of the market at these reservations:
    nothing when the book does not trade (goods_market.clear)."""
    count = len(res)
    sold = numpy.zeros(count)
    if count == 0:
        return sold, 0.0, 0.0
    order = numpy.argsort(res, kind="mergesort")
    asks = numpy.zeros(count)
    quantities = numpy.zeros(count)
    supply = 0.0
    for position in range(count):
        ask = res[order[position]]
        if has_minimum and ask < minimum:
            ask = minimum
        asks[position] = ask
        quantities[position] = qty[order[position]]
        supply += quantities[position]
    wanted = kernels.total_wanted(asks[0], floors, flexibles, budgets, references, exponents, maximums, capped)
    if not (wanted > 0.0 and supply > ROUNDING_SHARE * wanted):
        return sold, 0.0, 0.0
    taken, cost, sold_ordered, requested, flow = kernels.allocate_arrays(
        asks, quantities, floors, flexibles, budgets, references, exponents, maximums, capped, tier_bounds)
    traded = 0.0
    for position in range(count):
        sold[order[position]] = sold_ordered[position]
        traded += sold_ordered[position]
    if not traded > 0.0:
        return numpy.zeros(count), 0.0, 0.0
    return sold, requested, traded


@njit(**KERNEL)
def searched_floors(res0, res, qty, is_producer, cost, crowd, expected_sales, rate, spoilage):
    """unsold_search._floors: (whether each offer is searched, its floor)."""
    count = len(res)
    searched = numpy.zeros(count, dtype=numpy.bool_)
    floors = numpy.zeros(count)
    if numpy.isnan(rate):
        return searched, floors
    for i in range(count):
        opened = res0[i] <= 0.0 < res[i]
        if res[i] != res0[i] and not opened and not crowd[i]:
            continue
        if not is_producer[i]:
            continue
        held = queued_holding_value(res0[i], qty[i], expected_sales[i], rate, spoilage)
        floor = max(min(cost[i], max(res0[i], 0.0)), held)
        if res[i] > floor:
            searched[i] = True
            floors[i] = floor
    return searched, floors


@njit(**KERNEL)
def any_unsold(searched, sold, keys, qty, key_count):
    """True when some searched offer's (seller, tile) sold less than the offer holds (unsold_search._unsold)."""
    key_sold = numpy.zeros(key_count)
    for i in range(len(sold)):
        key_sold[keys[i]] += sold[i]
    for i in range(len(sold)):
        if searched[i] and key_sold[keys[i]] < qty[i] * (1.0 - ROUNDING_SHARE):
            return True
    return False


@njit(**KERNEL)
def flood_price(held, lowest, has_lowest, highest, floors, flexibles, budgets, references, exponents, maximums, capped):
    """unsold_search.flood_price over the buyers' arrays."""
    if not has_lowest or not 0.0 < lowest < highest:
        return highest
    ratio = (highest / lowest) ** (1.0 / (FLOOD_POINTS - 1))
    prices = numpy.zeros(FLOOD_POINTS)
    earnings = numpy.zeros(FLOOD_POINTS)
    best = -numpy.inf
    for step in range(FLOOD_POINTS):
        prices[step] = lowest * ratio ** step if step < FLOOD_POINTS - 1 else highest
        wanted = kernels.total_wanted(prices[step], floors, flexibles, budgets, references, exponents, maximums, capped)
        earnings[step] = prices[step] * min(held, wanted)
        best = max(best, earnings[step])
    level = -numpy.inf
    for step in range(FLOOD_POINTS):
        if earnings[step] >= best * (1.0 - FLOOD_TIE) and prices[step] > level:
            level = prices[step]
    return level


@njit(**KERNEL)
def search_down(res, qty, searched, floors, keys, key_count, minimum, has_minimum, buyer_floors, flexibles, budgets,
                references, exponents, maximums, capped, tier_bounds):
    """unsold_search.search_asks after the salvage floors: the reservations with the searched asks brought down to the
    highest common level at which they sell out or sit at their floors."""
    count = len(res)
    low = numpy.inf
    for i in range(count):
        if searched[i]:
            low = min(low, floors[i])
    distinct = True
    held = 0.0
    for i in range(count):
        if searched[i]:
            held += qty[i]
            if floors[i] != low:
                distinct = False
    unique = True
    seen = numpy.zeros(key_count, dtype=numpy.bool_)
    for i in range(count):
        if searched[i]:
            if seen[keys[i]]:
                unique = False
            seen[keys[i]] = True
    level = low
    shortcut = False
    if distinct and unique:
        price = max(low, minimum) if has_minimum else low
        wanted = kernels.total_wanted(price, buyer_floors, flexibles, budgets, references, exponents, maximums, capped)
        shortcut = wanted * (1.0 + UNSOLD_BOUND_MARGIN) < held * (1.0 - ROUNDING_SHARE)
    if not shortcut:
        level = kernels.search_level(res, qty, searched, floors, keys, key_count, minimum, has_minimum, buyer_floors,
                                     flexibles, budgets, references, exponents, maximums, capped, tier_bounds)
    kept = res.copy()
    for i in range(count):
        if searched[i]:
            kept[i] = min(res[i], max(floors[i], level))
    return kept


@njit(**KERNEL)
def salvage_and_search(res, qty, searched, floors, keys, key_count, minimum, has_minimum, buyer_floors, flexibles, budgets,
                       references, exponents, maximums, capped, tier_bounds):
    """unsold_search._salvage_floors, then search_asks when any searched ask is still above its floor."""
    count = len(res)
    held = 0.0
    highest = -numpy.inf
    for i in range(count):
        if searched[i] and floors[i] <= 0.0:
            held += qty[i]
            highest = max(highest, res[i])
    if held > 0.0:
        level = flood_price(held, minimum, has_minimum, highest, buyer_floors, flexibles, budgets, references, exponents,
                            maximums, capped)
        for i in range(count):
            if searched[i] and floors[i] <= 0.0:
                floors[i] = level
        for i in range(count):
            if searched[i] and not res[i] > floors[i]:
                searched[i] = False
    for i in range(count):
        if searched[i]:
            return search_down(res, qty, searched, floors, keys, key_count, minimum, has_minimum, buyer_floors, flexibles,
                               budgets, references, exponents, maximums, capped, tier_bounds)
    return res.copy()


@njit(**KERNEL)
def raise_up(res, qty, is_producer, cost, share, multiple, minimum, has_minimum, buyer_floors, flexibles, budgets,
             references, exponents, maximums, capped):
    """unsold_search.raise_sold_out's raise (demand_search.raise_asks): the producers' asks lifted to the highest common level
    at which the buyers still ask for all that is offered, each held to the band above its cost."""
    count = len(res)
    limits = numpy.full(count, numpy.inf)
    any_limit = False
    any_raisable = False
    lowest = numpy.inf
    supply = 0.0
    for i in range(count):
        supply += qty[i]
        if is_producer[i]:
            any_raisable = True
            lowest = min(lowest, res[i])
            if numpy.isfinite(cost[i]):
                limits[i] = band_edge(cost[i], share[i], multiple[i])
                any_limit = True
    if not any_raisable:
        return res.copy()
    if not kernels.covers_at(res, qty, numpy.full(count, -1.0), minimum, has_minimum, buyer_floors, flexibles, budgets,
                             references, exponents, maximums, capped):
        return res.copy()
    money = 0.0
    highest = 0.0
    for bid in range(len(buyer_floors)):
        money += max(0.0, budgets[bid])
        highest = max(highest, maximums[bid])
    ceiling = min(highest, money / supply if supply > 0.0 else numpy.inf)
    if lowest <= 0.0 or not numpy.isfinite(ceiling) or ceiling <= lowest:
        return res.copy()
    if any_limit:
        top = -numpy.inf
        for i in range(count):
            if is_producer[i]:
                top = max(top, limits[i])
        ceiling = min(ceiling, top)
        if ceiling <= lowest:
            return res.copy()
    level = kernels.raise_search(res, qty, is_producer, limits, lowest, ceiling, minimum, has_minimum, buyer_floors,
                                 flexibles, budgets, references, exponents, maximums, capped)
    if level < 0.0:
        return res.copy()
    lifted = res.copy()
    for i in range(count):
        if is_producer[i]:
            lifted[i] = max(res[i], min(level, limits[i]))
    return lifted


@njit(**KERNEL)
def decide_market(has_bids, res0, qty, is_producer, cost, share, expected, workshops, crowd, expected_sales, multiple, keys,
                  size, rate, spoilage, minimum, has_minimum, buyer_floors, flexibles, budgets, references, exponents, maximums, capped,
                  tier_bounds, intensity, grid_count, grid_start, grid_step, months, discount_rate):
    """The reservations of one market's offers after the sellers' re-pricing, the unsold search and the sold-out raise."""
    count = len(res0)
    key_count = 0 if count == 0 else keys[count - 1] + 1
    if has_bids:      # a market nobody bids in keeps its asks (strategic_offers returns them), but the search still lowers them
        res = choose_asks(res0, qty, is_producer, cost, share, expected, workshops, crowd, expected_sales, multiple, size,
                          intensity, grid_count, grid_start, grid_step, months, discount_rate)
    else:
        res = res0.copy()
    sold, requested, traded = clear_figures(res, qty, minimum, has_minimum, buyer_floors, flexibles, budgets, references,
                                            exponents, maximums, capped, tier_bounds)
    searched, floors = searched_floors(res0, res, qty, is_producer, cost, crowd, expected_sales, rate, spoilage)
    anything = False
    for i in range(count):
        if searched[i]:
            anything = True
    if anything and any_unsold(searched, sold, keys, qty, key_count):
        res = salvage_and_search(res, qty, searched, floors, keys, key_count, minimum, has_minimum, buyer_floors, flexibles,
                                 budgets, references, exponents, maximums, capped, tier_bounds)
        sold, requested, traded = clear_figures(res, qty, minimum, has_minimum, buyer_floors, flexibles, budgets,
                                                references, exponents, maximums, capped, tier_bounds)
    if traded >= requested * (1.0 - ROUNDING_SHARE):
        return res
    return raise_up(res, qty, is_producer, cost, share, multiple, minimum, has_minimum, buyer_floors, flexibles, budgets,
                    references, exponents, maximums, capped)


@njit(**KERNEL)
def decide_markets(has_bids, offer_ptr, res0, qty, is_producer, cost, share, expected, workshops, crowd, expected_sales, multiple,
                   keys, size, rate, spoilage, minimum, has_minimum, bid_ptr, buyer_floors, flexibles, budgets, references,
                   exponents, maximums, capped, tier_ptr, tier_values, intensity, grid_count, grid_start, grid_step,
                   months, discount_rate):
    """Every market's final reservations (`decide_market`), one after another, in the order of `res0`."""
    final = res0.copy()
    for market in range(len(offer_ptr) - 1):
        o0, o1 = offer_ptr[market], offer_ptr[market + 1]
        b0, b1 = bid_ptr[market], bid_ptr[market + 1]
        final[o0:o1] = decide_market(
            has_bids[market], res0[o0:o1], qty[o0:o1], is_producer[o0:o1], cost[o0:o1], share[o0:o1], expected[o0:o1], workshops[o0:o1],
            crowd[o0:o1], expected_sales[o0:o1], multiple[o0:o1], keys[o0:o1], size[market], rate[market], spoilage[market],
            minimum[market], has_minimum[market], buyer_floors[b0:b1], flexibles[b0:b1], budgets[b0:b1], references[b0:b1],
            exponents[b0:b1], maximums[b0:b1], capped[market], tier_values[tier_ptr[market]:tier_ptr[market + 1]], intensity,
            grid_count, grid_start, grid_step, months, discount_rate)
    return final
