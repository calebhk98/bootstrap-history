"""Money payments made as posting rows from lists of names and amounts, without a `Transfer` object each.

`post_payments` numbers the names as `book.transfer_many` does (the payers, then the payees, then the currencies), purposes as it
encodes them, applies the rows as one all-or-none batch, and on a refusal posts the same payments through the object path so the
book raises the error it always has."""
from typing import Sequence

from sim.book_apply import RULE_BATCH
from sim.book_post import table_from
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.book_types import Transfer
from sim.compiled_tables.causes import OK


def post_payments(book, payers: Sequence[str], payees: Sequence[str], currencies: Sequence[str], amounts: Sequence[float],
                  purposes: Sequence[str]) -> None:
    """Apply the payments (parallel sequences) as one batch."""
    if not len(payers):
        return
    if not hasattr(book, "apply_postings"):       # a stand-in book without posting tables
        book.transfer_many([Transfer(*each) for each in zip(payers, payees, currencies, amounts, purposes)])
        return
    payer_numbers = book._agent_numbers(payers)
    payee_numbers = book._agent_numbers(payees)
    currency_numbers = book._admit_currencies(currencies)
    codes = [book.purposes.encode(purpose) for purpose in purposes]
    table = table_from(TRANSFER_POSTINGS, TransferPostings, len(payers), payer_numbers, payee_numbers, currency_numbers, list(amounts),
                       [code for code, _reference in codes], [reference for _code, reference in codes], [0] * len(payers))
    outcomes, _scratch = book.apply_postings(table, table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, 0, *([] for _each in range(9))), 1, RULE_BATCH, stop_on_refusal=True)
    if int(outcomes.code[0]) != OK:
        book.transfer_many([Transfer(*each) for each in zip(payers, payees, currencies, amounts, purposes)])

