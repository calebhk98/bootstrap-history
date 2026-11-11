"""`goods_settle.settle_good` for a good whose markets all traded in the batch: one kernel call (`goods_settle_kernel.settle_good_markets`).

The Python side reserves room before the call and again when the kernel says a table is too small or a purpose is not numbered (the
kernel writes nothing then); a book that refuses the settlement, or a market not in the batch, leaves the good to the unfused path."""
from collections import namedtuple
from typing import Dict, Optional

import numpy

from sim.book_settled import reserve_for_settlement, settlement_plans

from .goods_settle_kernel import NEEDS_PURPOSE, NEEDS_ROOM, NO_CODE, NO_PAIRS, SETTLED, settle_good_markets
from .year_ledger_tables import SETTLEMENTS

# The settled columns a `GoodSettlement` reads afterwards, by listed agent (cut by `agent_offset`) and by key (cut by `key_offset`).
SettledColumns = namedtuple("SettledColumns", ("agent_offset", "agent", "goods_in", "got_goods", "buyer_net", "paid_as_buyer", "key_offset",
                                               "key_holder", "key_tile", "key_to_mint"))
NO_NUMBERS = numpy.zeros(0, dtype=numpy.int64)
ATTEMPTS = 4      # a call may need room, then a purpose, then room again


def _numbers(book, names) -> numpy.ndarray:
    """The book numbers of the accounts it has numbered."""
    if not names:
        return NO_NUMBERS
    numbers = book.agent_ids.numbers
    return numpy.array([numbers[name] for name in names if name in numbers], dtype=numpy.int64)


def reserve_for(book, tables, keys: int, batch_agents: int, rows: int, money_across: bool) -> None:
    """Room for a settlement of that size on the book and in the ledger's pair tables (what the unfused path reserved as it went)."""
    reserve_for_settlement(book, batch_agents, keys)
    tables.pairs["received"].reserve(rows)
    tables.pairs["sold"].reserve(rows)
    if money_across:
        tables.pairs["imports_paid"].reserve(rows)
        tables.pairs["exports_received"].reserve(rows)


def settle_in_one_call(record, ledger, cleared, good: str, plant_makers: Dict[str, list]):
    """(delivered per market, settled columns, markets that traded, the buyers the respend reads, whether the mint was given goods) of the
    good, or None when the unfused path has to settle it; `NO_PAIRS` when nothing was to settle."""
    book, tables, batch = record.book, ledger.tables, cleared.batch
    if batch is None:
        return None
    tables.flush(SETTLEMENTS)
    tables.fit_agents()
    bids, offers = batch.orders.tables()
    pack = batch.pack
    good_number, currency_number = book.good_number(good), book.currency_number(cleared.context.setup.currency_id)
    makers = numpy.array(sorted(book.agent_ids.numbers[name] for name in plant_makers.get(good, ()) if name in book.agent_ids.numbers),
                         dtype=numpy.int64)
    codes = book.purposes.find("sale of %s" % good) or (NO_CODE, NO_CODE)
    imports, exports = _numbers(book, ledger.import_accounts), _numbers(book, ledger.export_accounts)
    across = len(imports) > 0 or len(exports) > 0          # else no money can cross the border: the kernel is given no tables for it
    pairs = tables.pairs
    for _attempt in range(ATTEMPTS):
        answer = settle_good_markets(
            cleared.quantity, cleared.way, cleared.slots, batch.pair_ptr, batch.pair_bid, batch.pair_offer, batch.pair_quantity, batch.ask,
            pack.bid_rows, pack.offer_rows, bids.buyer, bids.tile, offers.seller, offers.tile, len(book.tile_ids) + 1,
            book.tile_ids.numbers.get("", -1), good_number, currency_number, imports, exports, makers, codes[0], codes[1], book.tables(),
            settlement_plans(book), tables.figures, tables.counters, pairs["received"].target(), pairs["sold"].target(),
            pairs["imports_paid"].target() if across else None, pairs["exports_received"].target() if across else None)
        status = answer[0]
        if status == NEEDS_ROOM:
            reserve_for(book, tables, *answer[1:5])
        elif status == NEEDS_PURPOSE:
            codes = book.purposes.encode("sale of %s" % good)
        else:
            break
    if status == NO_PAIRS:
        return NO_PAIRS
    if status != SETTLED:
        return None
    (_status, _keys, _agents, _rows, _across, delivered, positions, agent_offset, agent, goods_in, got_goods, buyer_net, paid_as_buyer,
     bought_place, bought_agent, bought_units, bought_money, any_to_mint, key_offset, key_holder, key_tile, key_to_mint) = answer
    settled = SettledColumns(agent_offset, agent, goods_in, got_goods, buyer_net, paid_as_buyer, key_offset, key_holder, key_tile, key_to_mint)
    return delivered, settled, positions, (bought_place, bought_agent, bought_units, bought_money), any_to_mint
