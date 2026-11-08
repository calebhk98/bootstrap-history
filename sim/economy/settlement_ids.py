"""A good's traded markets settled from the order tables by ids: no `KeyTable`, no (agent, tile) names, no `Settlement` objects.

`settle_by_ids` does what `settlement_arrays.settle_results` did for the traded markets of one `TableBatch`: the pairs of the
markets (the batch's `GoodsPairs` rows) are read as agent and tile numbers from the bid and offer tables, the (agent, tile)
keys and the agents are numbered in the order `settlement_batch.KeyTable` numbered them (the used bids' keys by bid place, the used
offers' keys by offer place, then the keys of buyers with no tile, who take delivery where the seller holds the goods), each market
is settled on the purses and stocks the earlier ones left (`settlement_batch_kernel.settle_markets`), and the sums are applied on the
book once (`book_settled.post_settled_by_numbers`: the gross totals and the good's flow as `Book.post_settled` records them).

The answer is columns by market (`SettledByIds`): for each listed agent its book number and sums, for each key its holder and
tile, cut by market with offsets, in the order a `Settlement` listed them."""
from collections import namedtuple
from typing import FrozenSet, Optional

import numpy

from sim.book_read_kernels import find_slots, read_stocks_at
from sim.book_settled import post_settled_by_numbers

from .settlement_batch_kernel import settle_markets
from .settlement_numbering import local_numbering

# Columns of a good's settled markets. `pair_offset`, `agent_offset` and `key_offset` cut the concatenations by traded market
# (market i owns entries offset[i]:offset[i + 1]); the per-agent columns are `Settlement.paid` and the rest, with `agent` the book
# number of the listed agent; the per-key columns say whose goods on which tile (book numbers); `delivered` is the goods moved by
# each market.
SettledByIds = namedtuple("SettledByIds", (
    "pair_offset", "agent_offset", "key_offset", "agent", "paid", "received", "goods_in", "goods_out", "buyer_net", "got_goods",
    "paid_as_buyer", "imports", "exports", "key_holder", "key_tile", "key_to_mint", "delivered"))


def pair_positions(pair_ptr: numpy.ndarray, slots: numpy.ndarray) -> tuple:
    """(pairs per market, the batch positions of all those markets' pairs one market after another) for the markets `slots`."""
    starts, ends = pair_ptr[slots], pair_ptr[slots + 1]
    sizes = ends - starts
    total = int(sizes.sum())
    before = numpy.cumsum(sizes) - sizes
    return sizes, numpy.repeat(starts - before, sizes) + numpy.arange(total, dtype=numpy.int64)


def first_use_numbers(values: numpy.ndarray) -> tuple:
    """(the number of each value in order of first appearance, the distinct values in that order)."""
    distinct, first, inverse = numpy.unique(values, return_index=True, return_inverse=True)
    order = numpy.argsort(first, kind="stable")
    rank = numpy.empty(len(distinct), dtype=numpy.int64)
    rank[order] = numpy.arange(len(distinct), dtype=numpy.int64)
    return rank[inverse.reshape(-1)], distinct[order]


def numbered_keys(batch, positions: numpy.ndarray, tile_stride: int, empty_tile: int, bids, offers) -> tuple:
    """(receipt key of each pair, selling key of each pair, holder and tile of each key, agent of each key within the batch's
    agents, the batch's agents as book numbers) numbered in the order `KeyTable` took them."""
    pack = batch.pack
    bid_at, offer_at = batch.pair_bid[positions], batch.pair_offer[positions]
    bid_row, offer_row = pack.bid_rows[bid_at], pack.offer_rows[offer_at]
    buyer, buyer_tile = bids.buyer[bid_row], bids.tile[bid_row]
    seller, seller_tile = offers.seller[offer_row], offers.tile[offer_row]
    used_bids, used_offers = pack.bid_rows[numpy.unique(bid_at)], pack.offer_rows[numpy.unique(offer_at)]
    tileless = buyer_tile == empty_tile
    receipt_tile = numpy.where(tileless, seller_tile, buyer_tile)       # a buyer with no tile takes delivery where the seller holds the goods
    key_value = lambda holder, tile: holder * tile_stride + tile        # noqa: E731
    candidates = numpy.concatenate((key_value(bids.buyer[used_bids], bids.tile[used_bids]),
                                    key_value(offers.seller[used_offers], offers.tile[used_offers]),
                                    key_value(buyer[tileless], seller_tile[tileless])))
    _numbers, keys = first_use_numbers(candidates)
    sorted_order = numpy.argsort(keys, kind="stable")
    place_in = lambda values: sorted_order[numpy.searchsorted(keys[sorted_order], values)]      # noqa: E731
    receipt, sold_from = place_in(key_value(buyer, receipt_tile)), place_in(key_value(seller, seller_tile))
    holder, tile = keys // tile_stride, keys % tile_stride
    key_agent, agents = first_use_numbers(holder)
    return receipt, sold_from, holder, tile, key_agent, agents


def settle_by_ids(book, batch, slots: numpy.ndarray, currency: str, item: str, purpose: str,
                  import_accounts: FrozenSet[str], export_accounts: FrozenSet[str]) -> Optional[SettledByIds]:
    """Settle the traded markets `slots` of the batch (in this order) on the book; None when they have no pairs."""
    sizes, positions = pair_positions(batch.pair_ptr, slots)
    if not len(positions):
        return None
    bids, offers = batch.orders.tables()
    tile_stride = len(book.tile_ids) + 1
    empty_tile = book.tile_ids.numbers.get("", -1)
    receipt, sold_from, holder, tile, key_agent, agents = numbered_keys(batch, positions, tile_stride, empty_tile, bids, offers)
    (pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local) = local_numbering(
        sizes, receipt, sold_from, key_agent, len(agents))
    good, currency_number = book.good_number(item), book.currency_number(currency)
    stock_state = numpy.zeros(len(holder))
    sellers = numpy.unique(sold_from)
    slots_held = find_slots(book.stock_rows.table, book.stock_rows.index, holder[sellers], good, tile[sellers])
    stock_state[sellers] = read_stocks_at(book.stock_rows.table, slots_held)
    cash_state = book.balances_at(agents, currency)
    flags = book.agent_table
    answer = settle_markets(
        pair_offset, agent_offset, key_offset, buyer_key, seller_key, batch.pair_quantity[positions], batch.ask[batch.pair_offer[positions]],
        key_agent_local, key_global, agent_global, stock_state, cash_state, flags.is_edge[agents] != 0, flags.is_mint[agents] != 0,
        flags.is_external[agents] != 0, _in_accounts(book, agents, import_accounts), _in_accounts(book, agents, export_accounts), True, True)
    (goods, _money, _payer, paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports, exports, _given, _taken,
     key_to_mint, batch_paid, batch_received, batch_given, batch_taken) = answer
    post_settled_by_numbers(book, currency, purpose, item, currency_number, good, agents, batch_paid, batch_received, holder, tile, batch_given,
                            batch_taken)
    delivered = numpy.array([goods[first:last].sum() for first, last in zip(pair_offset[:-1].tolist(), pair_offset[1:].tolist())])
    return SettledByIds(pair_offset, agent_offset, key_offset, agents[agent_global], paid, received, goods_in, goods_out, buyer_net,
                        got_goods, paid_as_buyer, imports, exports, holder[key_global], tile[key_global], key_to_mint, delivered)


def _in_accounts(book, agents: numpy.ndarray, accounts: FrozenSet[str]) -> numpy.ndarray:
    """Per agent number: whether it is one of the customs `accounts` (names)."""
    numbers = book.agent_ids.numbers
    return numpy.isin(agents, numpy.array([numbers[name] for name in accounts if name in numbers], dtype=numpy.int64))
