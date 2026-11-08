"""The keep holders pay for the bonded people who work for them (`bondage_hours.place_held`), posted as rows.

The rows of `bondage_rows.KeepRows` become one batch of money postings (a holder pays a cohort), all or none, applied by the book's
kernel; the names are numbered as `Book.transfer_many` numbered them (the payers, then the payees, then the currency). The payers' costs
go to the year's ledger as one block. A batch the book refuses is posted again as `Transfer` records, which raises the book's own error."""
from sim.book_apply import RULE_BATCH
from sim.book_post import table_from
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.compiled_tables.causes import OK

from .bondage_rows import KeepRows
from .types import Transfer

KEEP_PURPOSE = "keep of bonded"


def post_keep(book, ledger, keep: KeepRows, currency: str) -> None:
    """Pay the keep: one batch on the book, and each payer's cost in the ledger's money out. Nothing to pay posts nothing."""
    count = len(keep)
    if not count:
        return
    amounts = keep.amounts.tolist()
    if hasattr(book, "apply_postings"):
        code, reference = book.purposes.encode(KEEP_PURPOSE)
        payers, payees = book._agent_numbers(keep.employers), book._agent_numbers(keep.cohorts)
        currencies = book._admit_currencies([currency] * count)
        postings = table_from(TRANSFER_POSTINGS, TransferPostings, count, payers, payees, currencies, amounts, [code] * count,
                              [reference] * count, [0] * count)
        outcomes, _scratch = book.apply_postings(postings, table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, 0, *([] for _each in range(9))),
                                                 1, RULE_BATCH, stop_on_refusal=True)
        refused = int(outcomes.row_count[0]) != 1 or int(outcomes.code[0]) != OK
    else:
        refused = True
    if refused:      # the object path raises the error the book has always raised
        book.transfer_many([Transfer(employer, cohort, currency, amount, KEEP_PURPOSE)
                            for employer, cohort, amount in zip(keep.employers, keep.cohorts, amounts)])
    ledger.add_money_out(ledger.tables.agent_numbers(keep.employers), keep.amounts)
