"""The route search of many merchants at once, rows sorted, as two compiled calls (`merchants_book_kernel.search_goods` over a
matrix of merchants: `search_blocks`, then `sorted_rows`).

`seen` holds one row per merchant: the price each merchant counts in every slot (0.0 where it knows none). Merchants that
count the same prices in a good's slots get the same rows for that good, so the search runs once for them. Each merchant's
rows come back sorted as `merchants_book.search` sorts them: by rank, then good, then source area id, then destination area
id (two stable sorts, which is what `numpy.lexsort` gives). Only full searches (every good, every source) are made here. A
good with a pair whose holding years were not known is searched again, for every merchant, once they are.
"""
import numpy as np

from sim.jit import njit

from .merchants_book_kernel import _grown
from .merchants_kernel import search_into


@njit
def price_hash(bits, merchant, slot, size):
    """A wrapping integer hash of the bits of a merchant's `size` prices from `slot` (`bits`: the prices of every merchant
    read as integers), used only to find merchants that may count the same prices."""
    total = np.int64(0)
    for place in range(size):
        total += bits[merchant, slot + place] * np.int64(2 * place + 1)
    return total


@njit
def search_blocks(seen, redo, slot_base, area_count, pair_base, order_base, cost_flat, nearest_flat, years_flat, id_order_flat, spoilage,
                  unit_mass_kg, interest_rate, margin_share, kilograms_per_tonne, stored_source, stored_destination, stored_rank,
                  stored_price_here, stored_outlay, stored_ceiling, stored, block_start, block_count):
    """Search each merchant's slots of every good where `redo[merchant, good]`, one search for all the merchants that count the same prices,
    and keep the rows by (merchant, good) block: `block_start` and `block_count` place the block in the stored arrays (grown here,
    after the `stored` rows already kept). Returns the arrays, the new `stored` and a flag for each pair of `years_flat` whose
    holding years were needed and not known, and for each (merchant, good) whether it
    needed any (`dirty`: it must be searched again once they are known)."""
    count_merchants = seen.shape[0]
    bits = seen.view(np.int64)
    count_goods = area_count.shape[0]
    widest = 1
    for good in range(count_goods):
        widest = max(widest, area_count[good])
    missing = np.zeros(years_flat.shape[0], np.bool_)
    scratch_source = np.empty(widest * widest, np.int64)
    scratch_destination = np.empty(widest * widest, np.int64)
    scratch_rank = np.empty(widest * widest, np.float64)
    scratch_price_here = np.empty(widest * widest, np.float64)
    scratch_outlay = np.empty(widest * widest, np.float64)
    scratch_ceiling = np.empty(widest * widest, np.float64)
    every_source = np.ones(widest, np.bool_)
    hashes = np.zeros((count_merchants, count_goods), np.int64)
    dirty = np.zeros((count_merchants, count_goods), np.bool_)
    flagged = np.zeros(1, np.int64)
    for merchant in range(count_merchants):
        for good in range(count_goods):
            if not redo[merchant, good]:
                continue
            size = area_count[good]
            slot = slot_base[good]
            prices = seen[merchant, slot:slot + size]
            hashes[merchant, good] = price_hash(bits, merchant, slot, size)
            twin = -1
            for earlier in range(merchant):
                if hashes[earlier, good] == hashes[merchant, good]:
                    same = True
                    for place in range(size):
                        if seen[earlier, slot + place] != prices[place]:
                            same = False
                            break
                    if same:
                        twin = earlier
                        break
            if twin >= 0:
                block_start[merchant, good] = block_start[twin, good]
                block_count[merchant, good] = block_count[twin, good]
                dirty[merchant, good] = dirty[twin, good]
                continue
            pair = pair_base[good]
            order = order_base[good]
            found = search_into(prices, cost_flat[pair:pair + size * size].reshape((size, size)),
                                nearest_flat[order:order + size], years_flat[pair:pair + size * size].reshape((size, size)), id_order_flat[order:order + size],
                                every_source[:size], interest_rate, spoilage[good], unit_mass_kg[good], margin_share,
                                kilograms_per_tonne, scratch_source, scratch_destination, scratch_rank, scratch_price_here,
                                scratch_outlay, scratch_ceiling, missing[pair:pair + size * size], flagged)
            dirty[merchant, good] = flagged[0] > 0
            flagged[0] = 0
            if stored + found > stored_source.shape[0]:
                capacity = max(2 * stored_source.shape[0], stored + found)
                stored_source = _grown(stored_source, capacity)
                stored_destination = _grown(stored_destination, capacity)
                stored_rank = _grown(stored_rank, capacity)
                stored_price_here = _grown(stored_price_here, capacity)
                stored_outlay = _grown(stored_outlay, capacity)
                stored_ceiling = _grown(stored_ceiling, capacity)
            for row in range(found):
                stored_source[stored + row] = scratch_source[row]
                stored_destination[stored + row] = scratch_destination[row]
                stored_rank[stored + row] = scratch_rank[row]
                stored_price_here[stored + row] = scratch_price_here[row]
                stored_outlay[stored + row] = scratch_outlay[row]
                stored_ceiling[stored + row] = scratch_ceiling[row]
            block_start[merchant, good] = stored
            block_count[merchant, good] = found
            stored += found
    return (stored_source, stored_destination, stored_rank, stored_price_here, stored_outlay, stored_ceiling, stored, missing, dirty)


@njit
def sorted_rows(area_count, order_base, id_rank_flat, stored_source, stored_destination, stored_rank, stored_price_here,
                stored_outlay, stored_ceiling, block_start, block_count):
    """The rows of every merchant one after another, each merchant's sorted as `merchants_book.search` sorts them: by rank, then
    good, source area id and destination area id. Returns the rows per merchant, then good, source position, destination
    position, rank, price here, outlay and most it pays of all of them."""
    count_merchants = block_count.shape[0]
    count_goods = block_count.shape[1]
    widest = 1
    for good in range(count_goods):
        widest = max(widest, area_count[good])
    counts = np.zeros(count_merchants, np.int64)
    for merchant in range(count_merchants):
        for good in range(count_goods):
            counts[merchant] += block_count[merchant, good]
    total = counts.sum()
    out_good = np.empty(total, np.int64)
    out_source = np.empty(total, np.int64)
    out_destination = np.empty(total, np.int64)
    out_rank = np.empty(total, np.float64)
    out_price_here = np.empty(total, np.float64)
    out_outlay = np.empty(total, np.float64)
    out_ceiling = np.empty(total, np.float64)
    place = 0
    for merchant in range(count_merchants):
        rows = counts[merchant]
        row_good = np.empty(rows, np.int64)
        row_from = np.empty(rows, np.int64)
        keys = np.empty(rows, np.int64)
        position = 0
        for good in range(count_goods):
            for row in range(block_count[merchant, good]):
                at = block_start[merchant, good] + row
                row_good[position] = good
                row_from[position] = at
                source_rank = id_rank_flat[order_base[good] + stored_source[at]]
                destination_rank = id_rank_flat[order_base[good] + stored_destination[at]]
                keys[position] = (good * widest + source_rank) * widest + destination_rank
                position += 1
        by_id = np.argsort(keys, kind="mergesort")
        ranks = np.empty(rows, np.float64)
        for position in range(rows):
            ranks[position] = stored_rank[row_from[by_id[position]]]
        by_rank = np.argsort(ranks, kind="mergesort")
        for position in range(rows):
            chosen = by_id[by_rank[position]]
            at = row_from[chosen]
            out_good[place + position] = row_good[chosen]
            out_source[place + position] = stored_source[at]
            out_destination[place + position] = stored_destination[at]
            out_rank[place + position] = stored_rank[at]
            out_price_here[place + position] = stored_price_here[at]
            out_outlay[place + position] = stored_outlay[at]
            out_ceiling[place + position] = stored_ceiling[at]
        place += rows
    return counts, out_good, out_source, out_destination, out_rank, out_price_here, out_outlay, out_ceiling
