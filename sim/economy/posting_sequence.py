"""Many book postings made one after another, applied in one kernel call.

A caller that used to call `book.post(transfers, moves)` (or `transfer`, `transfer_many`, `move_many`) once per exit, stake or
payment hands the whole sequence to `post_in_order`. Each step is its own batch, all or none, applied in the order given on the
balances the earlier steps left, and its names are numbered when its step is turned into rows, in step order: the book ends as it
did when the steps were posted one by one. A refused step stops the sequence; it is then posted through the object path, which
raises the error the book has always raised."""
from typing import List, Sequence, Tuple

from sim.book_apply import RULE_BATCH, RULE_SINGLE
from sim.book_post import table_from
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.book_types import GoodsMove, Transfer, delivery_tile
from sim.compiled_tables.causes import OK

Step = Tuple[Sequence[Transfer], Sequence[GoodsMove]]


def _transfer_rows(book, steps: Sequence[Step]):
    """The steps' transfers as one posting table, a batch per step. A step's names are numbered as `book.transfer_many` numbers
    them (the payers, then the payees, then the currencies), step after step."""
    payers, payees, currencies, amounts, codes, references, batches = [], [], [], [], [], [], []
    encode = book.purposes.encode
    for batch, (transfers, _moves) in enumerate(steps):
        payers += book._agent_numbers([transfer.payer for transfer in transfers])
        payees += book._agent_numbers([transfer.payee for transfer in transfers])
        currencies += book._admit_currencies([transfer.currency for transfer in transfers])
        amounts += [transfer.amount for transfer in transfers]
        for transfer in transfers:
            code, reference = encode(transfer.purpose)
            codes.append(code)
            references.append(reference)
        batches += [batch] * len(transfers)
    return table_from(TRANSFER_POSTINGS, TransferPostings, len(payers), payers, payees, currencies, amounts, codes, references, batches)


def _move_rows(book, steps: Sequence[Step]):
    """The steps' goods moves as one posting table, a batch per step, numbered as `book.move_many` numbers them."""
    givers, receivers, goods, tiles, receiver_tiles, quantities, codes, references, batches = ([] for _each in range(9))
    if not any(moves for _transfers, moves in steps):
        return table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, 0, *([] for _each in range(9)))
    encode = book.purposes.encode
    for batch, (_transfers, moves) in enumerate(steps):
        givers += book._agent_numbers([move.giver for move in moves])
        receivers += book._agent_numbers([move.receiver for move in moves])
        numbers = book._admit_tiles([move.tile for move in moves] + [delivery_tile(move) for move in moves])
        goods += book._admit_goods([move.good for move in moves])
        tiles += numbers[:len(moves)]
        receiver_tiles += numbers[len(moves):]
        quantities += [move.quantity for move in moves]
        for move in moves:
            code, reference = encode(move.purpose)
            codes.append(code)
            references.append(reference)
        batches += [batch] * len(moves)
    return table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, len(givers), givers, receivers, goods, tiles, receiver_tiles, quantities,
                      codes, references, batches)


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
    outcomes, _scratch = book.apply_postings(_transfer_rows(book, steps), _move_rows(book, steps), len(steps), rule,
                                             stop_on_refusal=True)
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
