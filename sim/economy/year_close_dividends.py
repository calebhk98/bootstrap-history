"""The close's dividends from the kernel's rows to the book and to the year's property income.

`dividend_plan(...)` runs `year_close_dividend_kernels.dividend_rows` over the producers that pay and returns a `DividendPlan`.
`post_dividends(...)` turns its rows into one batch of transfer postings (`book.apply_postings`), numbering and encoding the
names in the order the postings meet them, as the book does for objects. `add_property_income(...)` adds the rows (and the payments
of producers that exited, which were posted as they happened) to the property-income dictionary in the order of the producer rows.
"""
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np

from sim.book_post import table_from
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.compiled_tables.causes import OK

from . import shares as producer_shares
from .types import Transfer
from .year_close_dividend_kernels import DIVIDEND, SHARE_DIVIDEND, add_in_order, dividend_rows
from .year_close_owners import Participants, owner_table, share_holders

DIVIDEND_PURPOSE = "dividend"


@dataclass
class DividendPlan:
    row: np.ndarray            # the producer row that pays (int64), rising
    payee: np.ndarray          # the participant paid (int64)
    amount: np.ndarray         # (float64)
    kind: np.ndarray           # DIVIDEND or SHARE_DIVIDEND (int64)


def dividend_plan(record, columns, dividend: np.ndarray, pay_rows: np.ndarray, participants: Participants) -> DividendPlan:
    """The payments of the producers in `pay_rows` (rows of `columns`, each with a dividend above zero)."""
    count = len(columns.ids)
    owners = owner_table(record, participants)
    holders = share_holders(record, columns.row, count, participants)
    owner_participant = np.zeros(count, dtype=np.int64)
    owner_tile = np.full(count, -1, dtype=np.int64)
    names = [columns.records[row].owner for row in pay_rows.tolist()]
    owner_participant[pay_rows] = [participants.of(name) for name in names]
    owner_tile[pay_rows] = [owners.tile_of_cohort.get(name, -1) for name in names]
    rows, payees, amounts, kinds = dividend_rows(
        pay_rows, dividend, holders.has_shares, holders.start, holders.participant, holders.share, owner_participant, owner_tile,
        owners.tile_start, owners.member_participant, owners.member_share, owners.tile_total, producer_shares.EPSILON)
    return DividendPlan(rows, payees, amounts, kinds)


def _numbers(book, names: Sequence[str]) -> np.ndarray:
    """The book's number for each name. The names it has not met are numbered as the book numbers a batch of them: together, in
    name order (`IdTable.admit` sorts the new names of one call)."""
    numbers = book.agent_ids.numbers
    for name in sorted({name for name in names if name not in numbers}):
        book.agent_number(name)
    return np.array([numbers[name] for name in names], dtype=np.int64)


def post_dividends(book, currency: str, plan: DividendPlan, ids: Sequence[str], participants: Participants) -> None:
    """The plan's payments as one all-or-none batch from the producers (`ids` by row) in `currency`. A refused batch raises what
    `book.transfer_many` raises for the same payments."""
    if not len(plan.row):
        return
    payer_names = [ids[row] for row in plan.row.tolist()]
    payers = _numbers(book, payer_names)
    first_seen = np.unique(plan.payee, return_index=True)
    in_order = first_seen[0][np.argsort(first_seen[1])].tolist()
    numbered = _numbers(book, [participants.names[each] for each in in_order]).tolist()
    book_number = dict(zip(in_order, numbered))
    payees = np.array([book_number[each] for each in plan.payee.tolist()], dtype=np.int64)
    currency_number = book.currency_number(currency)
    codes = {}
    for kind in _kinds_in_order(plan.kind):
        codes[kind] = book.purposes.encode(DIVIDEND_PURPOSE if kind == DIVIDEND else producer_shares.SHARE_DIVIDEND_PURPOSE)
    code = np.array([codes[kind][0] for kind in plan.kind.tolist()], dtype=np.int64)
    reference = np.array([codes[kind][1] for kind in plan.kind.tolist()], dtype=np.int64)
    rows = len(plan.row)
    transfers = table_from(TRANSFER_POSTINGS, TransferPostings, rows, payers, payees, np.full(rows, currency_number), plan.amount, code,
                           reference, np.zeros(rows, dtype=np.int64))
    moves = table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, 0, *[[] for _column in GOODS_MOVE_POSTINGS.columns])
    outcomes, _scratch = book.apply_postings(transfers, moves, 1)
    if int(outcomes.code[0]) != OK:
        book.transfer_many(as_transfers(plan, payer_names, participants, currency))      # the same refusal the objects would meet


def _kinds_in_order(kinds: np.ndarray) -> List[int]:
    """The kinds of row present, in the order each first appears."""
    order = []
    for kind in (DIVIDEND, SHARE_DIVIDEND):
        hits = np.flatnonzero(kinds == kind)
        if len(hits):
            order.append((int(hits[0]), kind))
    return [kind for _position, kind in sorted(order)]


def as_transfers(plan: DividendPlan, payer_names: Sequence[str], participants: Participants, currency: str) -> List[Transfer]:
    """The plan's rows as `Transfer` objects (for a test, or to report a refusal)."""
    purposes = {DIVIDEND: DIVIDEND_PURPOSE, SHARE_DIVIDEND: producer_shares.SHARE_DIVIDEND_PURPOSE}
    return [Transfer(payer, participants.names[payee], currency, amount, purposes[kind])
            for payer, payee, amount, kind in zip(payer_names, plan.payee.tolist(), plan.amount.tolist(), plan.kind.tolist())]


def add_property_income(property_income: Dict[str, float], participants: Participants, rows: np.ndarray, payees: np.ndarray,
                        amounts: np.ndarray) -> None:
    """`property_income[payee] = property_income.get(payee, 0.0) + amount` for each payment in the order of `rows` (stable: payments
    of one row keep their order), so each payee's sum and the order new payees enter the dictionary are what the loop made."""
    if not len(rows):
        return
    order = np.argsort(rows, kind="stable")
    payees, amounts = payees[order], amounts[order]
    totals = np.zeros(len(participants.names))
    for participant in np.unique(payees).tolist():
        totals[participant] = property_income.get(participants.names[participant], 0.0)
    add_in_order(payees, amounts, totals)
    unique, first = np.unique(payees, return_index=True)
    for participant in unique[np.argsort(first)].tolist():
        property_income[participants.names[participant]] = float(totals[participant])
