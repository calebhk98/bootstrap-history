"""The book's object posting as it was written before the single-posting fast paths: every name admitted as one list per column,
fresh posting tables per call, `apply_postings` for every batch. The reference `test_book_fast_paths.py` compares the book's
methods against. It uses only the book's public admit, table and kernel doors, so it stays valid while the methods change."""
from sim.book_apply import RULE_BATCH, RULE_SINGLE, apply_goods, apply_money
from sim.book_post import grown_scratch, table_from
from sim.book_tables import (GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings)
from sim.book_types import delivery_tile


def plain_transfer_table(book, transfers) -> TransferPostings:
    payers = book._admit_agents([each.payer for each in transfers]) if transfers else []
    payees = book._admit_agents([each.payee for each in transfers]) if transfers else []
    currencies = book._admit_currencies([each.currency for each in transfers])
    codes = [book.purposes.encode(each.purpose) for each in transfers]
    return table_from(TRANSFER_POSTINGS, TransferPostings, len(transfers), payers, payees, currencies,
                      [each.amount for each in transfers], [code for code, _reference in codes],
                      [reference for _code, reference in codes], [0] * len(transfers))


def plain_move_table(book, moves) -> GoodsMovePostings:
    givers = book._admit_agents([each.giver for each in moves]) if moves else []
    receivers = book._admit_agents([each.receiver for each in moves]) if moves else []
    numbers = book._admit_tiles([each.tile for each in moves] + [delivery_tile(each) for each in moves])
    codes = [book.purposes.encode(each.purpose) for each in moves]
    return table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, len(moves), givers, receivers,
                      book._admit_goods([each.good for each in moves]), numbers[:len(moves)], numbers[len(moves):],
                      [each.quantity for each in moves], [code for code, _reference in codes],
                      [reference for _code, reference in codes], [0] * len(moves))


def plain_post(book, transfers, moves, rule=RULE_BATCH) -> None:
    """One batch, as `Book.post` (RULE_BATCH) or `Book.transfer` / `Book.move` (RULE_SINGLE) posts it, raising the book's error."""
    transfer_table, move_table = plain_transfer_table(book, transfers), plain_move_table(book, moves)
    transfer_rows, move_rows = len(transfers), len(moves)
    if transfer_rows and move_rows:
        outcomes, scratch = book.apply_postings(transfer_table, move_table, 1, rule, stop_on_refusal=True)
        code, culprit = int(outcomes.code[0]), int(outcomes.culprit[0])
    else:
        book._reserve_for_moves(move_rows)
        book.scratch = scratch = grown_scratch(book.scratch, transfer_rows, move_rows)
        if transfer_rows:
            code, culprit = apply_money(transfer_table, 0, transfer_rows, book.money_tables(), scratch.money_plan,
                                        scratch.money_local, rule)
        else:
            code, culprit = apply_goods(move_table, 0, move_rows, book.goods_tables(), scratch.goods_plan, scratch.goods_local,
                                        rule)
    book._raise_for(code, culprit, scratch, transfer_table, move_table, rule)


def plain_transfer(book, transfer) -> None:
    if not transfer.amount >= 0.0 or transfer.amount != 0.0:
        plain_post(book, (transfer,), (), RULE_SINGLE)


def plain_move(book, move) -> None:
    if not move.quantity >= 0.0 or move.quantity != 0.0:
        plain_post(book, (), (move,), RULE_SINGLE)
