"""Many book postings made one after another, applied in one kernel call.

A caller that used to call `book.post(transfers, moves)` (or `transfer`, `transfer_many`, `move_many`) once per exit, stake or
payment hands the whole sequence to `post_in_order`. Each step is its own batch, all or none, applied in the order given on the
balances the earlier steps left, and its names are numbered when its step is turned into rows, in step order: the book ends as it
did when the steps were posted one by one. A refused step stops the sequence; it is then posted through the object path, which
raises the error the book has always raised."""
from typing import List, Sequence, Tuple

import numpy

from sim.book_apply import RULE_BATCH, RULE_SINGLE
from sim.book_tables import GoodsMovePostings, TransferPostings
from sim.book_types import GoodsMove, Transfer
from sim.compiled_tables.causes import OK

Step = Tuple[Sequence[Transfer], Sequence[GoodsMove]]


def _joined(table_type, tables: List):
    """One posting table whose rows are the rows of `tables` one after another."""
    rows = sum(int(each.row_count[0]) for each in tables)
    columns = [numpy.concatenate([getattr(each, name)[:int(each.row_count[0])] for each in tables]) for name in table_type._fields[2:]]
    return table_type(numpy.array([rows], dtype=numpy.int64), numpy.array([rows], dtype=numpy.int64), *columns)


def post_in_order(book, steps: Sequence[Step], rule: int = RULE_BATCH) -> None:
    """Apply each step (transfers, moves) as `book.post` would, in order. `rule` is RULE_BATCH for steps made with `post`,
    `transfer_many` and `move_many`, RULE_SINGLE for steps that were each one `transfer` or `move`."""
    steps = [(list(transfers), list(moves)) for transfers, moves in steps if len(transfers) or len(moves)]
    if not steps:
        return
    if not hasattr(book, "apply_postings"):       # a stand-in book without posting tables posts step by step
        for transfers, moves in steps:
            book.post(transfers, moves)
        return
    transfer_tables = [book._transfer_table(transfers, batch) for batch, (transfers, _moves) in enumerate(steps)]
    move_tables = [book._move_table(moves, batch) for batch, (_transfers, moves) in enumerate(steps)]
    outcomes, _scratch = book.apply_postings(_joined(TransferPostings, transfer_tables), _joined(GoodsMovePostings, move_tables),
                                             len(steps), rule, stop_on_refusal=True)
    done = int(outcomes.row_count[0])
    if done == len(steps) and int(outcomes.code[done - 1]) == OK:
        return
    refused = done - 1 if int(outcomes.code[done - 1]) != OK else done
    for transfers, moves in steps[refused:]:
        book.post(transfers, moves) if rule == RULE_BATCH else _post_singly(book, transfers, moves)


def _post_singly(book, transfers: Sequence[Transfer], moves: Sequence[GoodsMove]) -> None:
    for transfer in transfers:
        book.transfer(transfer)
    for move in moves:
        book.move(move)
