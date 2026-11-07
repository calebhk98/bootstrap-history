"""The book's batch methods: many postings or many reads in one call, over the book's arrays.

A mixin of `Book` (sim/book.py), which owns the layout. The numpy views here last for one call and are dropped
before any row or slot is added, because an array cannot grow while a view of it is alive.
"""
import math
from typing import Dict, List, Sequence, Tuple

import numpy

from sim.book_types import (EDGE_PREFIX, ROUNDING_SHARE, UNDERFLOW, AgentId, CurrencyId, GoodId, GoodsMove,
                            InsufficientFunds, InsufficientGoods, TileId)


class BookBatch:
    # ---- many reads ------------------------------------------------------------------------------

    def rows_of(self, agents: Sequence[AgentId]) -> numpy.ndarray:
        """Each agent's row, -1 for one the book has never seen."""
        get = self._row.get
        return numpy.array([get(agent, -1) for agent in agents], dtype=numpy.int64)

    def slots_of(self, good: GoodId, agents: Sequence[AgentId], tiles: Sequence[TileId]) -> numpy.ndarray:
        """Each (agent, tile)'s slot for the good, -1 where nothing was ever held there."""
        get = self._slot.get
        return numpy.array([get((agent, good, tile), -1) for agent, tile in zip(agents, tiles)], dtype=numpy.int64)

    def balances_of(self, agents: Sequence[AgentId], currency: CurrencyId) -> numpy.ndarray:
        """Each agent's balance in the currency (zero for one the book has never seen)."""
        column = self._balance.get(currency)
        if column is None:
            return numpy.zeros(len(agents))
        return self.balances_at(self.rows_of(agents), currency)

    def balances_at(self, rows: numpy.ndarray, currency: CurrencyId) -> numpy.ndarray:
        """Balances by row (rows of -1 read zero)."""
        column = self._balance.get(currency)
        if column is None:
            return numpy.zeros(len(rows))
        values = numpy.frombuffer(column, dtype=numpy.float64)
        found = numpy.where(rows >= 0, values[numpy.maximum(rows, 0)], 0.0)
        del values
        return found

    def stocks_of(self, good: GoodId, agents: Sequence[AgentId], tiles: Sequence[TileId]) -> numpy.ndarray:
        """Each (agent, tile)'s stock of the good (zero where nothing was ever held)."""
        return self.stocks_at(self.slots_of(good, agents, tiles))

    def stocks_at(self, slots: numpy.ndarray) -> numpy.ndarray:
        """Stocks by slot (slots of -1 read zero)."""
        if not len(slots):
            return numpy.zeros(0)
        values = numpy.frombuffer(self._qty, dtype=numpy.float64)
        found = numpy.where(slots >= 0, values[numpy.maximum(slots, 0)], 0.0) if len(values) else numpy.zeros(len(slots))
        del values
        return found

    # ---- many postings ---------------------------------------------------------------------------

    def move_many(self, moves) -> None:
        """`post((), moves)`: all of them or none, with the stocks and the records written in one pass."""
        moves = list(moves)
        if not moves:
            return
        quantities = self._qty
        slot_of = self._slot_of
        for key, value in self._goods_after(moves).items():
            quantities[slot_of(*key)] = value
        gross, by_purpose_of = self._gross_goods, self._goods_by_purpose
        for move in moves:
            quantity, good, giver, receiver = move.quantity, move.good, move.giver, move.receiver
            gross[good] = gross.get(good, 0.0) + quantity
            by_purpose = by_purpose_of.get(good)
            if by_purpose is None:
                by_purpose = by_purpose_of[good] = {}
            purpose = move.purpose
            by_purpose[purpose] = by_purpose.get(purpose, 0.0) + quantity
            if giver.startswith(EDGE_PREFIX):
                self._record_edge_goods(giver, good, quantity, quantity)
            if receiver.startswith(EDGE_PREFIX):
                self._record_edge_goods(receiver, good, quantity, -quantity)

    def post_settled(self, currency: CurrencyId, purpose: str, item: GoodId, agents: Sequence[AgentId],
                     paid: Sequence[float], received: Sequence[float], keys: Sequence[Tuple[AgentId, TileId]],
                     given: Sequence[float], taken: Sequence[float]) -> None:
        """Apply a market's settlement summed: each agent's money paid and received, each (agent, tile)'s `item` given and
        taken. The same entries, totals and edge records as posting every pair, with no object per pair; an overdraft
        beyond rounding that the batch makes or deepens is refused, with nothing applied."""
        paid_array = numpy.asarray(paid, dtype=numpy.float64)
        received_array = numpy.asarray(received, dtype=numpy.float64)
        given_array = numpy.asarray(given, dtype=numpy.float64)
        taken_array = numpy.asarray(taken, dtype=numpy.float64)
        money_at = numpy.flatnonzero((paid_array != 0.0) | (received_array != 0.0))
        goods_at = numpy.flatnonzero((given_array != 0.0) | (taken_array != 0.0))
        row_get, slot_get = self._row.get, self._slot.get
        money_rows = numpy.array([row_get(agents[position], -1) for position in money_at.tolist()], dtype=numpy.int64)
        slots = numpy.array([slot_get((keys[position][0], item, keys[position][1]), -1) for position in goods_at.tolist()],
                            dtype=numpy.int64)
        out, income = paid_array[money_at], received_array[money_at]
        start = self.balances_at(money_rows, currency)
        value = start - out + income
        is_edge_agent = numpy.array([agents[position].startswith(EDGE_PREFIX) for position in money_at.tolist()], dtype=numpy.bool_)
        failing = numpy.flatnonzero((value < numpy.minimum(0.0, start) - numpy.maximum(ROUNDING_SHARE * (out + income), UNDERFLOW))
                                    & ~is_edge_agent)
        if len(failing):
            position = int(failing[0])
            raise InsufficientFunds("%s would hold %.6g %s after the batch"
                                    % (agents[int(money_at[position])], value[position], currency))
        goods_out, goods_in = given_array[goods_at], taken_array[goods_at]
        goods_start = self.stocks_at(slots)
        goods_value = goods_start - goods_out + goods_in
        goods_edge = numpy.array([keys[position][0].startswith(EDGE_PREFIX) for position in goods_at.tolist()], dtype=numpy.bool_)
        failing = numpy.flatnonzero((goods_value < numpy.minimum(0.0, goods_start)
                                     - numpy.maximum(ROUNDING_SHARE * (goods_out + goods_in), UNDERFLOW)) & ~goods_edge)
        if len(failing):
            position = int(failing[0])
            agent, tile = keys[int(goods_at[position])]
            raise InsufficientGoods("%s would hold %.6g %s on %s after the batch" % (agent, goods_value[position], item, tile))
        if len(money_at):
            for index in numpy.flatnonzero(money_rows < 0).tolist():
                money_rows[index] = self._row_of(agents[int(money_at[index])])
            column = self._column(currency)
            values = numpy.frombuffer(column, dtype=numpy.float64)
            values[money_rows] = value
            del values
            seen = numpy.frombuffer(self._seen[currency], dtype=numpy.uint8)
            seen[money_rows] = 1
            del seen
        if len(goods_at):
            for index in numpy.flatnonzero(slots < 0).tolist():
                agent, tile = keys[int(goods_at[index])]
                slots[index] = self._slot_of(agent, item, tile)
            values = numpy.frombuffer(self._qty, dtype=numpy.float64)
            values[slots] = goods_value
            del values
        gross = self._gross_money
        gross[currency] = gross.get(currency, 0.0) + math.fsum(paid_array.tolist())
        for index in numpy.flatnonzero(is_edge_agent).tolist():
            self._record_edge_money(agents[int(money_at[index])], currency, float(out[index] + income[index]),
                                    float(out[index] - income[index]))
        moved = math.fsum(given_array.tolist())
        if moved > 0.0:
            self._gross_goods[item] = self._gross_goods.get(item, 0.0) + moved
            by_purpose = self._goods_by_purpose.get(item)
            if by_purpose is None:
                by_purpose = self._goods_by_purpose[item] = {}
            by_purpose[purpose] = by_purpose.get(purpose, 0.0) + moved
        for index in numpy.flatnonzero(goods_edge).tolist():
            self._record_edge_goods(keys[int(goods_at[index])][0], item, float(goods_out[index] + goods_in[index]),
                                    float(goods_out[index] - goods_in[index]))
