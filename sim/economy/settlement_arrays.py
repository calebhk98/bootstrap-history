"""A good's clearings settled straight from their allocation arrays (goods_year_results.py), without a `Pairing` per market.

The pairs of every consecutive clearing of one batch are cut out of the batch's pair arrays together; the (agent, tile) key of
each bid and offer that traded is looked up once for the whole batch (`settlement_batch.KeyTable`), not once per market. A
clearing that holds no arrays (one the old path cleared) is packed from its `Pairing`, in its place in the order.
"""
from typing import FrozenSet, List, Sequence

import numpy

from .goods_year_results import ArrayClearing
from .settlement_batch import KeyTable, Packed, pack_pairings, settle_packed
from .settlement_record import Settlement
from .types import AgentId, ClearingResult


def _pack_run(table: KeyTable, packed: Packed, run: Sequence[ArrayClearing]) -> None:
    """The pairs of consecutive clearings of one batch."""
    batch = run[0].batch
    markets = numpy.array([result.market for result in run], dtype=numpy.int64)
    starts, ends = batch.pair_ptr[markets], batch.pair_ptr[markets + 1]
    sizes = ends - starts
    total = int(sizes.sum())
    packed.sizes.extend(sizes.tolist())
    packed.sources.extend((lambda result=result: result.pairing) if size else None for result, size in zip(run, sizes.tolist()))
    if not total:
        return
    before = numpy.cumsum(sizes) - sizes
    position = numpy.repeat(starts - before, sizes) + numpy.arange(total, dtype=numpy.int64)
    bid_at, offer_at = batch.pair_bid[position], batch.pair_offer[position]
    bids, offers = batch.flat_bids, batch.flat_offers
    bid_key = numpy.zeros(len(bids), dtype=numpy.int64)
    tileless = numpy.zeros(len(bids), dtype=numpy.bool_)
    used = numpy.unique(bid_at)
    chosen = [bids[index] for index in used.tolist()]
    bid_key[used] = [table.key(bid.buyer, bid.tile) for bid in chosen]
    tileless[used] = [not bid.tile for bid in chosen]
    offer_key = numpy.zeros(len(offers), dtype=numpy.int64)
    used = numpy.unique(offer_at)
    offer_key[used] = [table.key(offers[index].seller, offers[index].tile) for index in used.tolist()]
    receipt = bid_key[bid_at]
    for pair in numpy.flatnonzero(tileless[bid_at]).tolist():      # a buyer with no tile takes delivery where the seller holds the goods
        receipt[pair] = table.key(bids[bid_at[pair]].buyer, offers[offer_at[pair]].tile)
    packed.receipt.append(receipt)
    packed.seller.append(offer_key[offer_at])
    packed.quantity.append(batch.pair_quantity[position])
    packed.ask.append(batch.ask[offer_at])


def settle_results(book, results: Sequence[ClearingResult], currency: str, item: str, purpose: str,
                   import_accounts: FrozenSet[AgentId], export_accounts: FrozenSet[AgentId]) -> List[Settlement]:
    """`settlement_batch.settle_many` of the results of one good, in order, the arrays of the clearings that hold them used as they are."""
    table = KeyTable()
    packed = Packed()
    index = 0
    while index < len(results):
        result = results[index]
        end = index + 1
        if isinstance(result, ArrayClearing):
            while end < len(results) and isinstance(results[end], ArrayClearing) and results[end].batch is result.batch:
                end += 1
            _pack_run(table, packed, results[index:end])
        else:
            single = pack_pairings(table, [result.pairing], True)
            packed.sizes.extend(single.sizes)
            packed.sources.extend(single.sources)
            packed.receipt.extend(single.receipt)
            packed.seller.extend(single.seller)
            packed.quantity.extend(single.quantity)
            packed.ask.extend(single.ask)
        index = end
    return settle_packed(book, table, packed, currency, item, purpose, True, import_accounts, export_accounts)
