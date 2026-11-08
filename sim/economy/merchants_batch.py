"""Every merchant's candidate rows for one pass (the credit requests, the year's orders), searched in one kernel call.

`prepare` searches for all the merchants it is given and keeps each one's rows on the `RoutePass`, with the expectations
and home tile they were searched for; `rows_for` hands them back to `merchants_plan` when the same merchant asks again with
the same rate and the same expectations, and says None otherwise (the caller then searches alone, as it always has).
The rows are the rows `merchants_book.search` gives: the same arithmetic over the same arrays.
"""
from typing import Optional, Sequence

import numpy as np

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import merchants_batch_kernel
from .merchants_book import MerchantRows, RoutePass, merchant_array


def search_many(route: RoutePass, expected: np.ndarray, home_tiles: Sequence[str], interest_rate: float,
                margin_share: float) -> "list[MerchantRows]":
    """The rows of `merchants_book.search` (every good, every source) for each row of `expected` (a merchant's expected prices
    by slot, NaN where it has none), the merchant being at the same row of `home_tiles`."""
    book = route.book
    carriage = route.carriage
    if len(home_tiles) == 0:
        return []
    news = np.stack([book.news_current(carriage, tile) for tile in home_tiles])
    seen = np.where(np.isnan(expected), np.where(news, route.view_prices, 0.0), expected)
    merchants = len(home_tiles)
    stored = [np.empty(4096, np.int64), np.empty(4096, np.int64)] + [np.empty(4096, np.float64) for _column in range(4)]
    count = 0
    block_start = np.zeros((merchants, len(book.goods)), np.int64)
    block_count = np.zeros((merchants, len(book.goods)), np.int64)
    redo = np.ones((merchants, len(book.goods)), np.bool_)
    while True:
        (*stored, count, missing, dirty) = merchants_batch_kernel.search_blocks(
            seen, redo, book.slot_base, book.area_count, book.pair_base, book.order_base, book.cost_flat, book.nearest_flat, book.years_flat,
            book.id_order_flat, book.spoilage, book.unit_mass_kg, float(interest_rate), float(margin_share), KILOGRAMS_PER_TONNE,
            *stored, count, block_start, block_count)
        if not missing.any():
            break
        redo = dirty
        book.fill_years(carriage, missing)
    (counts, good, source, destination, rank, price_here, outlay, ceiling) = merchants_batch_kernel.sorted_rows(
        book.area_count, book.order_base, book.id_rank_flat, *stored, block_start, block_count)
    source_slot = book.slot_base[good] + source
    destination_slot = book.slot_base[good] + destination
    ends = np.cumsum(counts)
    found = []
    for position in range(len(home_tiles)):
        low, high = int(ends[position] - counts[position]), int(ends[position])
        found.append(MerchantRows(good[low:high], source[low:high], destination[low:high], source_slot[low:high],
                                  destination_slot[low:high], rank[low:high], price_here[low:high], outlay[low:high],
                                  ceiling[low:high]))
    return found


def rows_for(route: RoutePass, agent_id, interest_rate, home_tile, expected) -> Optional[MerchantRows]:
    """The rows kept for this merchant when they were searched for this rate, home tile and expected prices."""
    kept = route.prepared.get(agent_id)
    if kept is None:
        return None
    rate, tile, prices, rows = kept
    if rate != interest_rate or tile != home_tile or not np.array_equal(prices, expected, equal_nan=True):
        return None
    return rows


def prepare(route: RoutePass, merchants: Sequence, interest_rate: float, margin_share: float) -> None:
    """Search ahead for these merchants (all of them in one call) and keep the rows on `route` for `merchants_plan`."""
    book = route.book
    expected = [merchant_array(book, merchant.expected_prices) for merchant in merchants]
    rows = search_many(route, np.stack(expected) if expected else np.zeros((0, book.slots)),
                       [merchant.home_tile for merchant in merchants], interest_rate, margin_share)
    for merchant, prices, merchant_rows in zip(merchants, expected, rows):
        route.prepared[merchant.agent_id] = (float(interest_rate), merchant.home_tile, prices, merchant_rows)
