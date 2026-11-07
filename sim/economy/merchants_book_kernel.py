"""The merchants' route search over every good at once and their commitment loops, as compiled loops over arrays.

A market is a slot: the slots of a good are its areas in the order the area map lists them, goods in sorted order
(`merchants_book.RouteBook`). `search_goods` runs `merchants_kernel.search_into` over each good the caller allows;
`commit_orders` and `commit_credit` walk the rows best first, each commit changing the room the next row sees (the
rule of `merchants_shares.room_left`); a merchant's order stays what it was, because the rows come in the order the
caller sorted them.
"""
import numpy as np

from sim.jit import njit

from .merchants_kernel import search_into


@njit
def search_goods(prices, good_allowed, source_allowed, slot_base, area_count, pair_base, order_base, cost_flat,
                 years_flat, id_order_flat, spoilage, unit_mass_kg, interest_rate, margin_share, kilograms_per_tonne):
    """The unsorted rows of every allowed good: (good, source position, destination position, rank, price here,
    outlay, most it pays) as arrays of the row count, and a flag for each (pair of years_flat) whose holding years were
    needed but not known. `pair_base` and `order_base` place a good's pack in `cost_flat`/`years_flat` and
    `id_order_flat`."""
    capacity = 4096
    rows_good = np.empty(capacity, np.int64)
    rows_source = np.empty(capacity, np.int64)
    rows_destination = np.empty(capacity, np.int64)
    rows_rank = np.empty(capacity, np.float64)
    rows_price_here = np.empty(capacity, np.float64)
    rows_outlay = np.empty(capacity, np.float64)
    rows_ceiling = np.empty(capacity, np.float64)
    missing = np.zeros(years_flat.shape[0], np.bool_)
    widest = 0
    for good in range(good_allowed.shape[0]):
        widest = max(widest, area_count[good])
    scratch_source = np.empty(widest * widest, np.int64)
    scratch_destination = np.empty(widest * widest, np.int64)
    scratch_rank = np.empty(widest * widest, np.float64)
    scratch_price_here = np.empty(widest * widest, np.float64)
    scratch_outlay = np.empty(widest * widest, np.float64)
    scratch_ceiling = np.empty(widest * widest, np.float64)
    count = 0
    for good in range(good_allowed.shape[0]):
        if not good_allowed[good]:
            continue
        size = area_count[good]
        slot = slot_base[good]
        pair = pair_base[good]
        order = order_base[good]
        found = search_into(prices[slot:slot + size], cost_flat[pair:pair + size * size].reshape((size, size)),
                            years_flat[pair:pair + size * size].reshape((size, size)), id_order_flat[order:order + size],
                            source_allowed[slot:slot + size], interest_rate, spoilage[good], unit_mass_kg[good],
                            margin_share, kilograms_per_tonne, scratch_source, scratch_destination, scratch_rank,
                            scratch_price_here, scratch_outlay, scratch_ceiling, missing[pair:pair + size * size])
        if count + found > capacity:
            capacity = max(2 * capacity, count + found)
            rows_good = _grown(rows_good, capacity)
            rows_source = _grown(rows_source, capacity)
            rows_destination = _grown(rows_destination, capacity)
            rows_rank = _grown(rows_rank, capacity)
            rows_price_here = _grown(rows_price_here, capacity)
            rows_outlay = _grown(rows_outlay, capacity)
            rows_ceiling = _grown(rows_ceiling, capacity)
        for row in range(found):
            rows_good[count + row] = good
            rows_source[count + row] = scratch_source[row]
            rows_destination[count + row] = scratch_destination[row]
            rows_rank[count + row] = scratch_rank[row]
            rows_price_here[count + row] = scratch_price_here[row]
            rows_outlay[count + row] = scratch_outlay[row]
            rows_ceiling[count + row] = scratch_ceiling[row]
        count += found
    return (rows_good[:count].copy(), rows_source[:count].copy(), rows_destination[:count].copy(),
            rows_rank[:count].copy(), rows_price_here[:count].copy(), rows_outlay[:count].copy(),
            rows_ceiling[:count].copy(), missing)


@njit
def _grown(array, capacity):
    bigger = np.empty(capacity, array.dtype)
    bigger[:array.shape[0]] = array
    return bigger


@njit
def room_of(destination, source, volumes, held, own_into, group_into, group_out, own_share, group_share,
            source_share):
    """Units a merchant may still bid for from the source slot into the destination slot (`merchants_shares.room_left`
    over arrays): `volumes` is NaN where a market's volume was never seen."""
    room = np.inf
    into_volume = volumes[destination]
    out_volume = volumes[source]
    if not np.isnan(into_volume):
        mine = own_share * into_volume - held[destination] - own_into[destination]
        everyone = group_share * into_volume - group_into[destination]
        room = everyone if everyone < mine else mine
    elif not np.isnan(out_volume):
        room = own_share * out_volume - held[destination] - own_into[destination]
    if not np.isnan(out_volume):
        limit = source_share * out_volume - group_out[source]
        if limit < room:
            room = limit
    return room if room > 0.0 else 0.0


@njit
def commit_orders(destinations, sources, outlays, remaining, volumes, held, own_into, group_into, group_out,
                  own_share, group_share, source_share):
    """The units bid for on each row, best row first, while cash remains: the lesser of what the cash buys and the
    room left. Adds them to the merchant's own and the group's commitments. Returns the units by row."""
    quantities = np.zeros(destinations.shape[0], np.float64)
    for row in range(destinations.shape[0]):
        if remaining <= 0.0:
            break
        room = room_of(destinations[row], sources[row], volumes, held, own_into, group_into, group_out, own_share,
                       group_share, source_share)
        wanted = remaining / outlays[row]
        quantity = room if room < wanted else wanted
        if quantity <= 0.0:
            continue
        own_into[destinations[row]] += quantity
        group_into[destinations[row]] += quantity
        group_out[sources[row]] += quantity
        quantities[row] = quantity
        remaining -= quantity * outlays[row]
    return quantities


@njit
def commit_credit(destinations, sources, ranks, outlays, cash, limit, volumes, held, own_into, group_into, group_out,
                  own_share, group_share, source_share):
    """What a merchant would borrow and the gain it expects on it (`merchants_credit.credit_request`): each row's room
    is bought with cash first, the rest with a loan up to `limit`, best row first. Returns (wanted, gain)."""
    remaining = cash if cash > 0.0 else 0.0
    wanted = 0.0
    gain = 0.0
    for row in range(destinations.shape[0]):
        destination = destinations[row]
        source = sources[row]
        outlay = outlays[row]
        room = room_of(destination, source, volumes, held, own_into, group_into, group_out, own_share, group_share,
                       source_share)
        if outlay > 0.0:
            affordable = remaining / outlay
            paid_by_cash = room if room < affordable else affordable
        else:
            paid_by_cash = room
        remaining -= paid_by_cash * outlay
        extra = (room - paid_by_cash) * outlay
        if extra <= 0.0 or np.isnan(extra):
            planned = paid_by_cash
        else:
            if limit - wanted < extra:
                extra = limit - wanted
            planned = paid_by_cash + (extra / outlay if outlay > 0.0 else 0.0)
        own_into[destination] += planned
        group_into[destination] += planned
        group_out[source] += planned
        if extra <= 0.0 or np.isnan(extra):
            continue
        wanted += extra
        gain += extra * -ranks[row]
        if wanted >= limit:
            break
    return wanted, gain
