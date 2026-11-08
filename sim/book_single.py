"""One posting on its own, without building posting tables: `Book.transfer`, `Book.move` and a one-posting `Book.post` write their
row into a pair of one-row tables the book keeps (`SinglePostings`) and call the same money or goods kernel the batch path calls.

The rows are what `_transfer_table` and `_move_table` would make, names numbered in the order they would admit them (payer, then
payee; both tiles as one batch), so the book comes out as the table path leaves it, a refused posting included.

A mixin of `Book` (sim/book.py), which owns the layout (sim/book_store.py)."""
from sim.book_apply import apply_goods, apply_money
from sim.book_post import grown_scratch
from sim.book_tables import (GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings)
from sim.book_types import GoodsMove, Transfer, delivery_tile


def one_row_table(spec, table_type, rows: int):
    """A table with room for one row and `rows` of them in use (0 or 1)."""
    return spec.new_table(table_type, 1, rows)


class SinglePostings:
    """The tables one posting is written into: a one-row transfer table, a one-row goods-move table, and an empty one of each (the
    other half of a money-only or goods-only batch, which the refusal text reads only when its own half is the cause)."""

    def __init__(self):
        self.transfer = one_row_table(TRANSFER_POSTINGS, TransferPostings, 1)
        self.move = one_row_table(GOODS_MOVE_POSTINGS, GoodsMovePostings, 1)
        self.no_transfers = one_row_table(TRANSFER_POSTINGS, TransferPostings, 0)
        self.no_moves = one_row_table(GOODS_MOVE_POSTINGS, GoodsMovePostings, 0)


class BookSingle:
    def _post_one_transfer(self, transfer: Transfer, rule: int) -> None:
        """One transfer as a batch of its own, by the rule given (`Book.transfer` and `Book.post` differ only in the rule)."""
        payer, payee = self.agent_number(transfer.payer), self.agent_number(transfer.payee)
        code, reference = self.purposes.encode(transfer.purpose)
        row = self.single_postings.transfer
        row.payer[0] = payer
        row.payee[0] = payee
        row.currency[0] = self.currency_number(transfer.currency)
        row.amount[0] = transfer.amount
        row.purpose_code[0] = code
        row.purpose_reference[0] = reference
        self.scratch = scratch = grown_scratch(self.scratch, 1, 0)
        code, culprit = apply_money(row, 0, 1, self.money_tables(), scratch.money_plan, scratch.money_local, rule)
        self._raise_for(code, culprit, scratch, row, self.single_postings.no_moves, rule)

    def _post_one_move(self, move: GoodsMove, rule: int) -> None:
        """One goods move as a batch of its own, by the rule given."""
        giver, receiver = self.agent_number(move.giver), self.agent_number(move.receiver)
        tile_numbers = self.tile_ids.numbers
        tile, receiver_tile = move.tile, delivery_tile(move)
        tile_number, receiver_tile_number = tile_numbers.get(tile), tile_numbers.get(receiver_tile)
        if tile_number is None or receiver_tile_number is None:
            tile_number, receiver_tile_number = self._admit_tiles([tile, receiver_tile])
        code, reference = self.purposes.encode(move.purpose)
        row = self.single_postings.move
        row.giver[0] = giver
        row.receiver[0] = receiver
        row.good[0] = self.good_number(move.good)
        row.tile[0] = tile_number
        row.receiver_tile[0] = receiver_tile_number
        row.quantity[0] = move.quantity
        row.purpose_code[0] = code
        row.purpose_reference[0] = reference
        self._reserve_for_moves(1)
        self.scratch = scratch = grown_scratch(self.scratch, 0, 1)
        code, culprit = apply_goods(row, 0, 1, self.goods_tables(), scratch.goods_plan, scratch.goods_local, rule)
        self._raise_for(code, culprit, scratch, self.single_postings.no_transfers, row, rule)
