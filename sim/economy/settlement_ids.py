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

from .few_ids import in_ids
from .settlement_batch_kernel import settle_markets
from .settlement_number_kernel import delivered_by_market, number_good

# Columns of a good's settled markets. `pair_offset`, `agent_offset` and `key_offset` cut the concatenations by traded market
# (market i owns entries offset[i]:offset[i + 1]); the per-agent columns are `Settlement.paid` and the rest, with `agent` the book
# number of the listed agent; the per-key columns say whose goods on which tile (book numbers); `delivered` is the goods moved by
# each market.
SettledByIds = namedtuple("SettledByIds", (
    "pair_offset", "agent_offset", "key_offset", "agent", "paid", "received", "goods_in", "goods_out", "buyer_net", "got_goods",
    "paid_as_buyer", "imports", "exports", "key_holder", "key_tile", "key_to_mint", "delivered"))


def settle_by_ids(book, batch, slots: numpy.ndarray, currency: str, item: str, purpose: str,
                  import_accounts: FrozenSet[str], export_accounts: FrozenSet[str]) -> Optional[SettledByIds]:
    """Settle the traded markets `slots` of the batch (in this order) on the book; None when they have no pairs."""
    if not (batch.pair_ptr[slots + 1] - batch.pair_ptr[slots]).any():
        return None
    bids, offers = batch.orders.tables()
    pack = batch.pack
    (positions, pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local, holder, tile,
     agents, sold_from) = number_good(batch.pair_ptr, slots, batch.pair_bid, batch.pair_offer, pack.bid_rows, pack.offer_rows, bids.buyer, bids.tile,
                           offers.seller, offers.tile, len(book.tile_ids) + 1, book.tile_ids.numbers.get("", -1))
    good, currency_number = book.good_number(item), book.currency_number(currency)
    stock_state = numpy.zeros(len(holder))
    sellers = numpy.flatnonzero(numpy.bincount(sold_from, minlength=1))     # the distinct keys sold from, ascending
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
    delivered = delivered_by_market(goods, pair_offset)
    return SettledByIds(pair_offset, agent_offset, key_offset, agents[agent_global], paid, received, goods_in, goods_out, buyer_net,
                        got_goods, paid_as_buyer, imports, exports, holder[key_global], tile[key_global], key_to_mint, delivered)


def _in_accounts(book, agents: numpy.ndarray, accounts: FrozenSet[str]) -> numpy.ndarray:
    """Per agent number: whether it is one of the customs `accounts` (names)."""
    numbers = book.agent_ids.numbers
    return in_ids(agents, [numbers[name] for name in accounts if name in numbers], len(book.agent_ids))
