"""Posting to the book: the Python methods `transfer`, `move`, `transfer_many` and `post`, and `apply_postings`, the one door a
converter holding posting tables uses.

The methods turn their objects into one batch of posting rows (names to ids, purposes to codes), call the kernel, and turn a
refusal back into the error the book has always raised. A converter that already holds ids builds the two tables itself
(`TRANSFER_POSTINGS`, `GOODS_MOVE_POSTINGS`, rows grouped by batch) and calls `apply_postings`; its refused batches come back
as rows of `BatchOutcomes`, and `refusal_of` names one.

A mixin of `Book` (sim/book.py), which owns the layout (sim/book_store.py)."""
from typing import Iterable, Sequence, Tuple

import numpy

from sim.book_apply import RULE_BATCH, RULE_SINGLE, apply_batches, apply_goods, apply_money
from sim.book_index import EMPTY, index_size_for, unpack_key
from sim.book_tables import (BATCH_OUTCOMES, BOOK_CAUSES, GOODS_MOVE_POSTINGS, INSUFFICIENT_FUNDS, INSUFFICIENT_GOODS, NEGATIVE_AMOUNT,
                             NEGATIVE_QUANTITY, PLANS, TRANSFER_POSTINGS, BatchOutcomes, GoodsMovePostings, Plans, Scratch,
                             TransferPostings)
from sim.book_types import (BookError, GoodsMove, InsufficientFunds, InsufficientGoods, NegativeAmount, Transfer,
                            delivery_tile)
from sim.compiled_tables.grouping import group_starts
from sim.compiled_tables.causes import OK
from sim.refusal import Refusal

MIN_PLAN_ROWS = 4


def plan_with_index(rows: int):
    """A plan with room for batches of that many posting rows (two cells each), and an empty hash index over it."""
    capacity = 2 * rows + MIN_PLAN_ROWS
    return PLANS.new_table(Plans, capacity), numpy.full(index_size_for(capacity), EMPTY, dtype=numpy.int64)


def new_scratch(money_rows: int, goods_rows: int) -> Scratch:
    """Plans (and their own hash indexes) with room for batches of that many transfer and goods-move rows."""
    return Scratch(*plan_with_index(money_rows), *plan_with_index(goods_rows))


def settled_scratch(money_entries: int, goods_entries: int) -> Scratch:
    """Plans for a summed settlement, one row per entry; it merges nothing, so its hash indexes are empty stubs."""
    stub = numpy.full(1, EMPTY, dtype=numpy.int64)
    return Scratch(PLANS.new_table(Plans, money_entries + 1), stub, PLANS.new_table(Plans, goods_entries + 1), stub)


def grown_settled(scratch: Scratch, money_entries: int, goods_entries: int) -> Scratch:
    """The settlement scratch itself when its plans have a row for every entry, else a bigger one."""
    if scratch is None or len(scratch.money_plan.key) <= money_entries or len(scratch.goods_plan.key) <= goods_entries:
        return settled_scratch(max(money_entries, 8), max(goods_entries, 8))
    return scratch


def grown_scratch(scratch: Scratch, money_rows: int, goods_rows: int) -> Scratch:
    """The scratch itself when its plans fit batches of that many rows, else one that does (a plan only ever grows)."""
    if scratch is None:
        return new_scratch(money_rows, goods_rows)
    money_fits = len(scratch.money_plan.key) >= 2 * money_rows + MIN_PLAN_ROWS
    goods_fits = len(scratch.goods_plan.key) >= 2 * goods_rows + MIN_PLAN_ROWS
    if money_fits and goods_fits:
        return scratch
    money = (scratch.money_plan, scratch.money_local) if money_fits else plan_with_index(max(money_rows, len(scratch.money_plan.key)))
    goods = (scratch.goods_plan, scratch.goods_local) if goods_fits else plan_with_index(max(goods_rows, len(scratch.goods_plan.key)))
    return Scratch(*money, *goods)


def table_from(spec, table_type, rows: int, *columns):
    """A posting table of `rows` rows from one sequence per column, in the spec's order."""
    return table_type(numpy.array([rows], dtype=numpy.int64), numpy.array([rows], dtype=numpy.int64),
                      *[numpy.array(values, dtype=column.dtype) for column, values in zip(spec.columns, columns)])


def largest_batch(starts: numpy.ndarray) -> int:
    return int(numpy.diff(starts).max()) if len(starts) > 1 else 0


class BookPostings:
    # ---- objects to rows -------------------------------------------------------------------------

    def _transfer_table(self, transfers: Sequence[Transfer], batch: int = 0) -> TransferPostings:
        """The transfers as posting rows of one batch; every name in them is admitted."""
        payers = self._agent_numbers([transfer.payer for transfer in transfers])
        payees = self._agent_numbers([transfer.payee for transfer in transfers])
        currencies = self._admit_currencies([transfer.currency for transfer in transfers])
        codes = [self.purposes.encode(transfer.purpose) for transfer in transfers]
        return table_from(TRANSFER_POSTINGS, TransferPostings, len(transfers), payers, payees, currencies,
                          [transfer.amount for transfer in transfers], [code for code, _reference in codes],
                          [reference for _code, reference in codes], [batch] * len(transfers))

    def _move_table(self, moves: Sequence[GoodsMove], batch: int = 0) -> GoodsMovePostings:
        """The goods moves as posting rows of one batch; every name in them is admitted."""
        givers = self._agent_numbers([move.giver for move in moves])
        receivers = self._agent_numbers([move.receiver for move in moves])
        numbers = self._admit_tiles([move.tile for move in moves] + [delivery_tile(move) for move in moves])
        codes = [self.purposes.encode(move.purpose) for move in moves]
        return table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, len(moves), givers, receivers,
                          self._admit_goods([move.good for move in moves]), numbers[:len(moves)], numbers[len(moves):],
                          [move.quantity for move in moves], [code for code, _reference in codes],
                          [reference for _code, reference in codes], [batch] * len(moves))

    def _agent_numbers(self, names: Sequence[str]) -> list:
        get = self.agent_ids.numbers.get
        numbers = [get(name) for name in names]
        if None in numbers:
            return self._admit_agents(names)
        return numbers

    # ---- the kernel calls ------------------------------------------------------------------------

    def apply_postings(self, transfers: TransferPostings, moves: GoodsMovePostings, batch_count: int, rule: int = RULE_BATCH,
                       stop_on_refusal: bool = False) -> Tuple[BatchOutcomes, Scratch]:
        """Apply batches 0 .. batch_count - 1 of the two posting tables (rows grouped by batch, batches rising; every id
        already admitted). Room for the rows a batch can make is reserved here. Returns the outcome of each batch
        (`BatchOutcomes`, `row_count` batches long) and the scratch plans (the last planned batch is still in them)."""
        transfer_rows, move_rows = int(transfers.row_count[0]), int(moves.row_count[0])
        self._reserve_for_moves(move_rows)
        if batch_count == 1:
            transfer_starts = numpy.array([0, transfer_rows], dtype=numpy.int64)
            move_starts = numpy.array([0, move_rows], dtype=numpy.int64)
            largest_transfers, largest_moves = transfer_rows, move_rows
        else:
            transfer_starts = group_starts(transfers.batch, transfer_rows, batch_count)
            move_starts = group_starts(moves.batch, move_rows, batch_count)
            largest_transfers, largest_moves = largest_batch(transfer_starts), largest_batch(move_starts)
        self.scratch = scratch = grown_scratch(self.scratch, largest_transfers, largest_moves)
        outcomes = BATCH_OUTCOMES.new_table(BatchOutcomes, max(batch_count, 1))
        apply_batches(transfers, transfer_starts, moves, move_starts, batch_count, self.tables(), scratch, outcomes, rule,
                      stop_on_refusal)
        return outcomes, scratch

    def _reserve_for_moves(self, move_rows: int) -> None:
        """Room for the stock slots, purpose flows and edge-goods rows that this many goods moves can make."""
        self.stock_rows.reserve(2 * move_rows)
        self.flow_rows.reserve(move_rows)
        self.edge_goods_rows.reserve(2 * move_rows)

    # ---- refusals --------------------------------------------------------------------------------

    def refusal_of(self, outcomes: BatchOutcomes, batch: int) -> Refusal:
        """The refusal for a batch that was not applied, its cause named and the offending cell in the facts."""
        code, culprit = int(outcomes.code[batch]), int(outcomes.culprit[batch])
        if code in (NEGATIVE_AMOUNT, NEGATIVE_QUANTITY):
            return BOOK_CAUSES.refusal(code, "the batch holds a negative amount", batch=batch, posting_row=culprit)
        if code == INSUFFICIENT_FUNDS:
            agent, currency = divmod(culprit, self.stride)
            names = (self.agent_ids.name(agent), self.currency_ids.name(currency))
            return BOOK_CAUSES.refusal(code, "%s would be overdrawn in %s" % names, batch=batch, agent=names[0], currency=names[1])
        if code == INSUFFICIENT_GOODS:
            agent, good, tile = unpack_key(culprit)
            names = (self.agent_ids.name(agent), self.good_ids.name(good), self.tile_ids.name(tile))
            return BOOK_CAUSES.refusal(code, "%s would be short of %s on %s" % names, batch=batch, agent=names[0], good=names[1],
                                       tile=names[2])
        return BOOK_CAUSES.refusal(code, "the book's tables were too small for the batch", batch=batch)

    def _failing_money(self, scratch: Scratch) -> list:
        """(agent name, currency name, balance after) for each money cell the planned batch overdrew."""
        plan = scratch.money_plan
        found = []
        for row in range(int(plan.row_count[0])):
            if plan.failing[row]:
                agent, currency = divmod(int(plan.key[row]), self.stride)
                found.append((self.agent_ids.name(agent), self.currency_ids.name(currency), float(plan.after[row]),
                              float(plan.before[row])))
        return found

    def _failing_stock(self, scratch: Scratch) -> list:
        """(agent, good, tile names, quantity after, quantity before) for each stock cell the planned batch overdrew."""
        plan = scratch.goods_plan
        found = []
        for row in range(int(plan.row_count[0])):
            if plan.failing[row]:
                agent, good, tile = unpack_key(int(plan.key[row]))
                found.append((self.agent_ids.name(agent), self.good_ids.name(good), self.tile_ids.name(tile),
                              float(plan.after[row]), float(plan.before[row])))
        return found

    def _raise_for(self, code: int, culprit: int, scratch: Scratch, transfers: TransferPostings, moves: GoodsMovePostings,
                   rule: int) -> None:
        """Raise the book's error for a refused batch (the one a method of this class posted), if it was refused."""
        if code == OK:
            return
        single = rule == RULE_SINGLE
        if code == NEGATIVE_AMOUNT:
            purpose = self.purposes.decode(int(transfers.purpose_code[culprit]), int(transfers.purpose_reference[culprit]))
            raise NegativeAmount("transfer of %r %s (%s) is negative%s" % (
                float(transfers.amount[culprit]), self.currency_ids.name(int(transfers.currency[culprit])), purpose,
                "; reverse payer and payee" if single else ""))
        if code == NEGATIVE_QUANTITY:
            purpose = self.purposes.decode(int(moves.purpose_code[culprit]), int(moves.purpose_reference[culprit]))
            raise NegativeAmount("move of %r %s (%s) is negative%s" % (
                float(moves.quantity[culprit]), self.good_ids.name(int(moves.good[culprit])), purpose,
                "; reverse giver and receiver" if single else ""))
        if code == INSUFFICIENT_FUNDS:
            agent, currency, after, before = min(self._failing_money(scratch))[:4]
            if single:
                purpose = self.purposes.decode(int(transfers.purpose_code[0]), int(transfers.purpose_reference[0]))
                raise InsufficientFunds("%s holds %.6g %s but must pay %.6g (%s)" % (agent, before, currency,
                                                                                    float(transfers.amount[0]), purpose))
            raise InsufficientFunds("%s would hold %.6g %s after the batch" % (agent, after, currency))
        if code == INSUFFICIENT_GOODS:
            agent, good, tile, after, before = min(self._failing_stock(scratch))
            if single:
                purpose = self.purposes.decode(int(moves.purpose_code[0]), int(moves.purpose_reference[0]))
                raise InsufficientGoods("%s holds %.6g %s on %s but must give %.6g (%s)" % (agent, before, good, tile,
                                                                                           float(moves.quantity[0]), purpose))
            raise InsufficientGoods("%s would hold %.6g %s on %s after the batch" % (agent, after, good, tile))
        raise BookError("the book's tables were too small for the posting (%s)" % BOOK_CAUSES.name(code))

    # ---- the book's methods ----------------------------------------------------------------------

    def _post_batch(self, transfers: Sequence[Transfer], moves: Sequence[GoodsMove], rule: int) -> None:
        transfer_table, move_table = self._transfer_table(transfers), self._move_table(moves)
        outcomes, scratch = self.apply_postings(transfer_table, move_table, 1, rule, stop_on_refusal=True)
        self._raise_for(outcomes, scratch, transfer_table, move_table, rule)

    def transfer(self, transfer: Transfer) -> None:
        """One transfer on its own: a payer that is not an edge account must hold the amount (less a rounding share) first.
        A zero amount does nothing."""
        if not transfer.amount >= 0.0 or transfer.amount != 0.0:
            self._post_batch((transfer,), (), RULE_SINGLE)

    def move(self, move: GoodsMove) -> None:
        """One goods move on its own, by the same rule as `transfer`."""
        if not move.quantity >= 0.0 or move.quantity != 0.0:
            self._post_batch((), (move,), RULE_SINGLE)

    def transfer_many(self, transfers: Iterable[Transfer]) -> None:
        self.post(transfers, ())

    def post(self, transfers: Iterable[Transfer], moves: Iterable[GoodsMove]) -> None:
        """Apply money transfers and goods moves together: all of them or none."""
        self._post_batch(list(transfers), list(moves), RULE_BATCH)

    def _post_batch(self, transfers: Sequence[Transfer], moves: Sequence[GoodsMove], rule: int) -> None:
        """One batch, by the narrowest kernel that holds it (money only, goods only, or both)."""
        transfer_table, move_table = self._transfer_table(transfers), self._move_table(moves)
        transfer_rows, move_rows = len(transfers), len(moves)
        if transfer_rows and move_rows:
            outcomes, scratch = self.apply_postings(transfer_table, move_table, 1, rule, stop_on_refusal=True)
            code, culprit = int(outcomes.code[0]), int(outcomes.culprit[0])
        else:
            self._reserve_for_moves(move_rows)
            self.scratch = scratch = grown_scratch(self.scratch, transfer_rows, move_rows)
            if transfer_rows:
                code, culprit = apply_money(transfer_table, 0, transfer_rows, self.money_tables(), scratch.money_plan,
                                            scratch.money_local, rule)
            else:
                code, culprit = apply_goods(move_table, 0, move_rows, self.goods_tables(), scratch.goods_plan,
                                            scratch.goods_local, rule)
        self._raise_for(code, culprit, scratch, transfer_table, move_table, rule)
