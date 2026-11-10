"""The year's wear and spoilage of every agent's goods and coin, as postings read from the book's tables.

`wear_and_spoilage(setup, record, durable_users)` is what the economy runs at the year's end: each stock that spoils loses its
good's yearly share to the spoilage account, each durable in use loses a service life's share to the consumption account, and coin
and metal lose their yearly share to the wear account. Both goods passes are worked out from the stocks as they stand before either
is booked; the kernel (wear_kernels.py) lists the losses in the order the Python sorted its moves, so the book is numbered and
filled as it was."""
from typing import List

import numpy as np

from sim.book_post import table_from
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.compiled_tables.causes import OK

from . import carriage_wear, metal_stock, types
from .types import GoodsMove
from .wear_kernels import loss_moves


def _ranks(names: List[str]) -> np.ndarray:
    """The place of each name (by number) among all the names, in sorted order."""
    ranks = np.empty(len(names), dtype=np.int64)
    ranks[sorted(range(len(names)), key=names.__getitem__)] = np.arange(len(names))
    return ranks


def _spoilage_share(spec) -> float:
    return min(1.0, max(0.0, spec.spoilage_per_year))


def _wear_share(spec) -> float:
    return min(1.0, max(0.0, 1.0 / spec.service_life_years if spec.service_life_years > 0.0 else 0.0))


def _share_by_good(book, specs, share_of_spec) -> np.ndarray:
    """Per good number of the book: the share the pass takes of a holding (zero for a good the specs do not name)."""
    shares = np.zeros(len(book.good_ids))
    numbers = book.good_ids.numbers
    for good, spec in specs.items():
        if good in numbers:
            shares[numbers[good]] = share_of_spec(spec)
    return shares


def _losses(book, order, shares, takes_part):
    """(giver numbers, good numbers, tile numbers, quantities) lost, read from the stock table now."""
    stocks = book.stock_rows.table
    agents, slots, lost = loss_moves(order, book.agent_table.first_slot, stocks, shares, takes_part,
                                     _ranks(book.good_ids.name_list), _ranks(book.tile_ids.name_list))
    return agents, stocks.good[slots], stocks.tile[slots], lost


def _post_losses(book, losses, receiver: str, purpose: str) -> None:
    """The losses as one all-or-none batch of moves from each giver to the `receiver` account."""
    agents, goods, tiles, lost = losses
    rows = len(agents)
    if not rows:
        return
    code, reference = book.purposes.encode(purpose)
    receiver_number = book.agent_number(receiver)
    moves = table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, rows, agents, np.full(rows, receiver_number), goods, tiles, tiles,
                       lost, np.full(rows, code), np.full(rows, reference), np.zeros(rows, dtype=np.int64))
    outcomes, _scratch = book.apply_postings(_no_transfers(), moves, 1)
    if int(outcomes.code[0]) != OK:
        names = book.agent_ids.name_list
        book.move_many([GoodsMove(names[giver], receiver, book.good_ids.name_list[good], book.tile_ids.name_list[tile], quantity,
                                  purpose) for giver, good, tile, quantity in zip(agents.tolist(), goods.tolist(), tiles.tolist(),
                                                                                  lost.tolist())])      # the book's own refusal


def _no_transfers() -> TransferPostings:
    return table_from(TRANSFER_POSTINGS, TransferPostings, 0, *[[] for _column in TRANSFER_POSTINGS.columns])


def _wear_coin(book, spec, order: np.ndarray) -> None:
    """Coin and metal lose their yearly share (metal_stock.wear_share): one transfer from each holder of more than zero."""
    worn = metal_stock.wear_share(spec)
    if worn is None:
        return
    share, purpose = worn
    balances = book.balances_at(order, spec.currency_id)
    paying = np.nonzero(balances > 0.0)[0]
    rows = len(paying)
    if not rows:
        return
    code, reference = book.purposes.encode(purpose)
    payee = book.agent_number(types.EDGE_WEAR)
    transfers = table_from(TRANSFER_POSTINGS, TransferPostings, rows, order[paying], np.full(rows, payee),
                           np.full(rows, book.currency_number(spec.currency_id)), balances[paying] * share, np.full(rows, code),
                           np.full(rows, reference), np.zeros(rows, dtype=np.int64))
    moves = table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, 0, *[[] for _column in GOODS_MOVE_POSTINGS.columns])
    outcomes, _scratch = book.apply_postings(transfers, moves, 1)
    if int(outcomes.code[0]) != OK:
        names = book.agent_ids.name_list
        book.transfer_many([types.Transfer(names[payer], types.EDGE_WEAR, spec.currency_id, amount, purpose)
                            for payer, amount in zip(order[paying].tolist(), (balances[paying] * share).tolist())])


def wear_and_spoilage(setup, record, durable_users=()) -> None:
    book = record.book
    names = book.agent_ids.name_list
    known = book.known_agent_numbers()
    order = np.array(sorted(known[book.agent_table.is_edge[known] == 0].tolist(), key=names.__getitem__), dtype=np.int64)
    fleets = {carriage_wear.account(merchant_id) for merchant_id in record.merchants}
    users = np.zeros(len(names), dtype=np.uint8)
    for name in set(record.cohorts) | set(durable_users) | fleets:
        number = book.agent_ids.numbers.get(name)
        if number is not None:
            users[number] = 1
    spoiled = _losses(book, order, _share_by_good(book, setup.specs, _spoilage_share), np.ones(len(names), dtype=np.uint8))
    worn = _losses(book, order, _share_by_good(book, setup.specs, _wear_share), users)
    _post_losses(book, spoiled, types.EDGE_SPOILAGE, "spoilage")
    _post_losses(book, worn, types.EDGE_CONSUMPTION, "wear")
    _wear_coin(book, record.currency, order)
