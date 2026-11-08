"""The book's batch methods: many reads or a summed settlement in one call, by name or by number.

A mixin of `Book` (sim/book.py), which owns the layout (sim/book_store.py). The numbers these return and take are the book's
own: an agent's number (-1 for a name the book does not know) and a stock slot (-1 for none). They are valid until the book is
loaded again."""
import math
from typing import Sequence, Tuple

import numpy

from sim.book_apply import apply_settled
from sim.book_commit import add_flow
from sim.book_post import grown_settled
from sim.book_read_kernels import find_slots, read_balances, read_stocks_at
from sim.book_tables import INSUFFICIENT_FUNDS, INSUFFICIENT_GOODS
from sim.book_types import (AgentId, BookError, CurrencyId, GoodId, InsufficientFunds, InsufficientGoods, TileId)
from sim.compiled_tables.causes import OK


class BookBatch:
    # ---- many reads ------------------------------------------------------------------------------

    def rows_of(self, agents: Sequence[AgentId]) -> numpy.ndarray:
        """Each agent's number, -1 for one the book has never seen (or has numbered but never held or paid anything)."""
        found = self.agent_ids.numbers_of(agents)
        return numpy.where((found >= 0) & (self.agent_table.known[found.clip(0)] != 0), found, -1)

    def slots_of(self, good: GoodId, agents: Sequence[AgentId], tiles: Sequence[TileId]) -> numpy.ndarray:
        """Each (agent, tile)'s slot for the good, -1 where nothing was ever held there."""
        number = self.good_ids.find(good)
        return find_slots(self.stock_rows.table, self.stock_rows.index, self.agent_ids.numbers_of(agents),
                          -1 if number is None else number, self.tile_ids.numbers_of(tiles))

    def balances_of(self, agents: Sequence[AgentId], currency: CurrencyId) -> numpy.ndarray:
        """Each agent's balance in the currency (zero for one the book has never seen)."""
        return self.balances_at(self.rows_of(agents), currency)

    def balances_at(self, rows: numpy.ndarray, currency: CurrencyId) -> numpy.ndarray:
        """Balances by agent number (numbers of -1 read zero)."""
        number = self.currency_ids.find(currency)
        return read_balances(self.balance_table, self.stride, numpy.asarray(rows, dtype=numpy.int64), -1 if number is None else number)

    def stocks_of(self, good: GoodId, agents: Sequence[AgentId], tiles: Sequence[TileId]) -> numpy.ndarray:
        """Each (agent, tile)'s stock of the good (zero where nothing was ever held)."""
        return self.stocks_at(self.slots_of(good, agents, tiles))

    def stocks_at(self, slots: numpy.ndarray) -> numpy.ndarray:
        """Stocks by slot (slots of -1 read zero)."""
        return read_stocks_at(self.stock_rows.table, numpy.asarray(slots, dtype=numpy.int64))

    # ---- many postings ---------------------------------------------------------------------------

    def move_many(self, moves) -> None:
        """`post((), moves)`: all of them or none."""
        moves = list(moves)
        if moves:
            self.post((), moves)

    def post_settled(self, currency: CurrencyId, purpose: str, item: GoodId, agents: Sequence[AgentId],
                     paid: Sequence[float], received: Sequence[float], keys: Sequence[Tuple[AgentId, TileId]],
                     given: Sequence[float], taken: Sequence[float]) -> None:
        """Apply a market's settlement summed: each agent's money paid and received, each (agent, tile)'s `item` given and
        taken. The same entries, totals and edge records as posting every pair, with no object per pair; an overdraft
        beyond rounding that the batch makes or deepens is refused, with nothing applied."""
        currency_number, good = self.currency_number(currency), self.good_number(item)
        paid_array, received_array = numpy.asarray(paid, dtype=numpy.float64), numpy.asarray(received, dtype=numpy.float64)
        given_array, taken_array = numpy.asarray(given, dtype=numpy.float64), numpy.asarray(taken, dtype=numpy.float64)
        money_agents = numpy.array(self._agent_numbers(list(agents)), dtype=numpy.int64)
        holders = numpy.array(self._agent_numbers([agent for agent, _tile in keys]), dtype=numpy.int64)
        tiles = numpy.array(self._admit_tiles([tile for _agent, tile in keys]), dtype=numpy.int64)
        self.stock_rows.reserve(len(keys))
        self.edge_goods_rows.reserve(len(keys))
        self.flow_rows.reserve(1)
        self.settled_plans = scratch = grown_settled(self.settled_plans, len(money_agents), len(keys))
        code, culprit = apply_settled(self.tables(), scratch, currency_number, money_agents, paid_array, received_array, holders,
                                      tiles, good, given_array, taken_array)
        if code != OK:
            self._raise_settled(code, scratch, currency, item)
        self._record_settled_totals(currency_number, good, purpose, paid_array, given_array)

    def _raise_settled(self, code: int, scratch, currency: CurrencyId, item: GoodId) -> None:
        """The error for a refused settlement: the first overdrawn entry in the order the market listed them."""
        if code == INSUFFICIENT_FUNDS:
            found = self._failing_money(scratch)
            raise InsufficientFunds("%s would hold %.6g %s after the batch" % (found[0][0], found[0][2], currency))
        if code == INSUFFICIENT_GOODS:
            found = self._failing_stock(scratch)
            raise InsufficientGoods("%s would hold %.6g %s on %s after the batch" % (found[0][0], found[0][3], item, found[0][2]))
        raise BookError("the book's tables were too small for the settlement")

    def _record_settled_totals(self, currency_number: int, good: int, purpose: str, paid: numpy.ndarray,
                               given: numpy.ndarray) -> None:
        """The gross totals and the purpose flow of a settlement: exact sums, added to the totals as the book always did."""
        currency_table = self.currency_table
        before = currency_table.gross_posted.item(currency_number) if currency_table.gross_seen.item(currency_number) else 0.0
        currency_table.gross_posted[currency_number] = before + math.fsum(paid.tolist())
        currency_table.gross_seen[currency_number] = 1
        moved = math.fsum(given.tolist())
        if moved > 0.0:
            good_table = self.good_table
            before = good_table.gross_moved.item(good) if good_table.gross_seen.item(good) else 0.0
            good_table.gross_moved[good] = before + moved
            good_table.gross_seen[good] = 1
            code, reference = self.purposes.encode(purpose)
            add_flow(self.flow_rows.table, self.flow_rows.index, good, code, reference, moved)

