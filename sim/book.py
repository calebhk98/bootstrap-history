"""The double-entry book: every agent's money (per currency) and goods (per good per tile).

It is a top-level module because both the economy's agents and the actors' purses (`sim/agents/purses.py`)
keep their holdings in a book of this one class.

Money and goods change hands only through `transfer` and `move` (or the batch forms), so each
posting has a counterparty. Edge accounts (`is_edge`) are the only ones that may go negative;
they are where the model meets what it does not simulate, and the sum over all accounts stays zero.

Layout: agents are numbered into rows once (a row is never reused). A currency's balances are one float array by row;
a stock is one slot in a flat float array, found by (agent, good, tile) through one dictionary read. The arrays are
`array.array` (single reads give plain floats) and the batch methods look at them as numpy arrays for the length of one
call, so no numpy view may be alive when a row or slot is added.
"""
import math
from array import array
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy

from sim.book_batch import BookBatch
from sim.book_record import BookRecord
from sim.book_types import (  # noqa: F401  (the names callers import from here)
    EDGE_EXCHANGE, EDGE_PREFIX, ROUNDING_SHARE, UNDERFLOW, AgentId, BookError, ConservationReport, CurrencyId,
    DeliveredMove, GoodId, GoodsMove, InsufficientFunds, InsufficientGoods, NegativeAmount, TileId, Transfer, delivery_tile,
    is_edge, _share)


class Book(BookBatch, BookRecord):
    def __init__(self):
        self._row: Dict[AgentId, int] = {}                    # agent to its row; an agent that left has none
        self._names: List[AgentId] = []                       # row to agent
        self._edge = bytearray()                              # row to 1 when the agent is an edge account
        self._balance: Dict[CurrencyId, array] = {}           # per currency, balance by row
        self._seen: Dict[CurrencyId, bytearray] = {}          # per currency, 1 where the row has ever been posted
        self._slot: Dict[Tuple[AgentId, GoodId, TileId], int] = {}
        self._qty = array("d")                                # stock by slot
        self._slot_key: List[object] = []                     # slot to (agent, good, tile); None for a slot given up
        self._slot_row = array("q")                           # slot to the holder's row, -1 once given up
        self._slot_good = array("q")                          # slot to the good's number
        self._good_number: Dict[GoodId, int] = {}
        self._tile_number: Dict[TileId, int] = {}
        self._slot_tile = array("q")
        self._agent_slots: Dict[AgentId, List[int]] = {}      # slots by holder, in the order they were made
        self._good_slots: Dict[GoodId, List[int]] = {}        # slots by good, in the order they were made
        self._gross_money: Dict[CurrencyId, float] = {}       # all postings ever, for conservation
        self._gross_goods: Dict[GoodId, float] = {}
        self._goods_by_purpose: Dict[GoodId, Dict[str, float]] = {}
        self._edge_money: Dict[Tuple[AgentId, CurrencyId], List[float]] = {}   # [gross volume, net] this year
        self._edge_goods: Dict[Tuple[AgentId, GoodId], List[float]] = {}
        self._supply_at_start: Dict[CurrencyId, float] = {}   # money supply when the year began

    # ---- numbering -----------------------------------------------------------------------------

    def _row_of(self, agent: AgentId) -> int:
        """The agent's row, made when it has none."""
        row = self._row.get(agent)
        if row is None:
            row = self._row[agent] = len(self._names)
            self._names.append(agent)
            self._edge.append(1 if agent.startswith(EDGE_PREFIX) else 0)
            for currency, column in self._balance.items():
                column.append(0.0)
                self._seen[currency].append(0)
        return row

    def _column(self, currency: CurrencyId) -> array:
        column = self._balance.get(currency)
        if column is None:
            column = self._balance[currency] = array("d", bytes(8 * len(self._names)))
            self._seen[currency] = bytearray(len(self._names))
        return column

    def _slot_of(self, agent: AgentId, good: GoodId, tile: TileId) -> int:
        """The slot holding the stock, made (at zero) when there is none."""
        key = (agent, good, tile)
        slot = self._slot.get(key)
        if slot is None:
            slot = self._slot[key] = len(self._slot_key)
            self._slot_key.append(key)
            self._qty.append(0.0)
            self._slot_row.append(self._row_of(agent))
            number = self._good_number.get(good)
            if number is None:
                number = self._good_number[good] = len(self._good_number)
            self._slot_good.append(number)
            tile_number = self._tile_number.get(tile)
            if tile_number is None:
                tile_number = self._tile_number[tile] = len(self._tile_number)
            self._slot_tile.append(tile_number)
            by_agent = self._agent_slots.get(agent)
            if by_agent is None:
                by_agent = self._agent_slots[agent] = []
            by_agent.append(slot)
            by_good = self._good_slots.get(good)
            if by_good is None:
                by_good = self._good_slots[good] = []
            by_good.append(slot)
        return slot

    def _put_money(self, agent: AgentId, currency: CurrencyId, value: float) -> None:
        row = self._row_of(agent)
        column = self._column(currency)
        column[row] = value
        self._seen[currency][row] = 1

    def _set_stock(self, agent: AgentId, good: GoodId, tile: TileId, value: float) -> None:
        self._qty[self._slot_of(agent, good, tile)] = value

    # ---- postings ------------------------------------------------------------------------------

    def transfer(self, transfer: Transfer) -> None:
        amount = transfer.amount
        if not amount >= 0.0:
            raise NegativeAmount("transfer of %r %s (%s) is negative; reverse payer and payee"
                                 % (amount, transfer.currency, transfer.purpose))
        if amount == 0.0:
            return
        payer, currency = transfer.payer, transfer.currency
        if not payer.startswith(EDGE_PREFIX):
            balance = self.balance(payer, currency)
            if balance < amount * (1.0 - ROUNDING_SHARE):
                raise InsufficientFunds("%s holds %.6g %s but must pay %.6g (%s)"
                                        % (payer, balance, currency, amount, transfer.purpose))
        for agent, signed in ((payer, -amount), (transfer.payee, amount)):
            row = self._row_of(agent)
            column = self._column(currency)
            column[row] += signed
            self._seen[currency][row] = 1
        self._record_money(transfer)

    def move(self, move: GoodsMove) -> None:
        quantity = move.quantity
        if not quantity >= 0.0:
            raise NegativeAmount("move of %r %s (%s) is negative; reverse giver and receiver"
                                 % (quantity, move.good, move.purpose))
        if quantity == 0.0:
            return
        giver = move.giver
        held = self.stock(giver, move.good, move.tile)
        if not giver.startswith(EDGE_PREFIX) and held < quantity * (1.0 - ROUNDING_SHARE):
            raise InsufficientGoods("%s holds %.6g %s on %s but must give %.6g (%s)"
                                    % (giver, held, move.good, move.tile, quantity, move.purpose))
        self._set_stock(giver, move.good, move.tile, held - quantity)
        delivery = delivery_tile(move)
        self._set_stock(move.receiver, move.good, delivery, self.stock(move.receiver, move.good, delivery) + quantity)
        self._record_goods(move)

    def transfer_many(self, transfers: Iterable[Transfer]) -> None:
        self.post(transfers, ())

    def post(self, transfers: Iterable[Transfer], moves: Iterable[GoodsMove]) -> None:
        """Apply money transfers and goods moves together: all of them or none."""
        transfers, moves = list(transfers), list(moves)
        money_after = self._money_after(transfers)
        goods_after = self._goods_after(moves)
        for (agent, currency), value in money_after.items():
            self._put_money(agent, currency, value)
        for (agent, good, tile), value in goods_after.items():
            self._set_stock(agent, good, tile, value)
        for transfer in transfers:
            self._record_money(transfer)
        for move in moves:
            self._record_goods(move)

    def _money_after(self, transfers: Sequence[Transfer]) -> Dict[Tuple[AgentId, CurrencyId], float]:
        after: Dict[Tuple[AgentId, CurrencyId], float] = {}
        before: Dict[Tuple[AgentId, CurrencyId], float] = {}
        moved: Dict[Tuple[AgentId, CurrencyId], float] = {}
        balance = self.balance
        for transfer in transfers:
            amount = transfer.amount
            currency = transfer.currency
            if not amount >= 0.0:
                raise NegativeAmount("transfer of %r %s (%s) is negative" % (amount, currency, transfer.purpose))
            key = (transfer.payer, currency)
            if key in after:
                after[key] -= amount
                moved[key] += amount
            else:
                start = before[key] = balance(*key)
                after[key] = start - amount
                moved[key] = amount
            key = (transfer.payee, currency)
            if key in after:
                after[key] += amount
                moved[key] += amount
            else:
                start = before[key] = balance(*key)
                after[key] = start + amount
                moved[key] = amount
        # only an overdraft this batch makes or deepens fails: a residue an earlier, larger batch
        # was allowed to leave is not this batch's doing
        failing = [key for key, value in after.items()
                   if value < min(0.0, before[key]) - max(ROUNDING_SHARE * moved[key], UNDERFLOW) and not is_edge(key[0])]
        if failing:
            agent, currency = min(failing)
            raise InsufficientFunds("%s would hold %.6g %s after the batch" % (agent, after[(agent, currency)], currency))
        return after

    def _goods_after(self, moves: Sequence[GoodsMove]) -> Dict[Tuple[AgentId, GoodId, TileId], float]:
        after: Dict[Tuple[AgentId, GoodId, TileId], float] = {}
        before: Dict[Tuple[AgentId, GoodId, TileId], float] = {}
        moved: Dict[Tuple[AgentId, GoodId, TileId], float] = {}
        slots, quantities = self._slot, self._qty
        for move in moves:
            quantity = move.quantity
            good = move.good
            if not quantity >= 0.0:
                raise NegativeAmount("move of %r %s (%s) is negative" % (quantity, good, move.purpose))
            key = (move.giver, good, move.tile)
            if key in after:
                after[key] -= quantity
                moved[key] += quantity
            else:
                slot = slots.get(key)
                start = before[key] = quantities[slot] if slot is not None else 0.0
                after[key] = start - quantity
                moved[key] = quantity
            key = (move.receiver, good, delivery_tile(move))
            if key in after:
                after[key] += quantity
                moved[key] += quantity
            else:
                slot = slots.get(key)
                start = before[key] = quantities[slot] if slot is not None else 0.0
                after[key] = start + quantity
                moved[key] = quantity
        failing = [key for key, value in after.items()
                   if value < min(0.0, before[key]) - max(ROUNDING_SHARE * moved[key], UNDERFLOW) and not is_edge(key[0])]
        if failing:
            agent, good, tile = min(failing)
            raise InsufficientGoods("%s would hold %.6g %s on %s after the batch" % (agent, after[(agent, good, tile)], good, tile))
        return after

    def _record_money(self, transfer: Transfer) -> None:
        amount, currency, payer, payee = transfer.amount, transfer.currency, transfer.payer, transfer.payee
        gross = self._gross_money
        gross[currency] = gross.get(currency, 0.0) + amount
        if payer.startswith(EDGE_PREFIX):
            self._record_edge_money(payer, currency, amount, amount)
        if payee.startswith(EDGE_PREFIX):
            self._record_edge_money(payee, currency, amount, -amount)

    def _record_edge_money(self, agent: AgentId, currency: CurrencyId, amount: float, signed: float) -> None:
        both = self._edge_money.get((agent, currency))
        if both is None:
            self._edge_money[(agent, currency)] = [amount, signed]
        else:
            both[0] += amount
            both[1] += signed

    def _record_goods(self, move: GoodsMove) -> None:
        quantity, good, giver, receiver = move.quantity, move.good, move.giver, move.receiver
        gross = self._gross_goods
        gross[good] = gross.get(good, 0.0) + quantity
        by_purpose = self._goods_by_purpose.get(good)
        if by_purpose is None:
            by_purpose = self._goods_by_purpose[good] = {}
        purpose = move.purpose
        by_purpose[purpose] = by_purpose.get(purpose, 0.0) + quantity
        if giver.startswith(EDGE_PREFIX):
            self._record_edge_goods(giver, good, quantity, quantity)
        if receiver.startswith(EDGE_PREFIX):
            self._record_edge_goods(receiver, good, quantity, -quantity)

    def _record_edge_goods(self, agent: AgentId, good: GoodId, quantity: float, signed: float) -> None:
        both = self._edge_goods.get((agent, good))
        if both is None:
            self._edge_goods[(agent, good)] = [quantity, signed]
        else:
            both[0] += quantity
            both[1] += signed

    # ---- reads ---------------------------------------------------------------------------------

    def balance(self, agent: AgentId, currency: CurrencyId) -> float:
        column = self._balance.get(currency)
        if column is None:
            return 0.0
        row = self._row.get(agent)
        return 0.0 if row is None else column[row]

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        slot = self._slot.get((agent, good, tile))
        return 0.0 if slot is None else self._qty[slot]

    def knows(self, agent: AgentId) -> bool:
        """Whether the agent has ever held or paid anything in this book."""
        return agent in self._row

    def holdings(self, agent: AgentId) -> dict:
        row = self._row.get(agent)
        money = {}
        if row is not None:
            for currency in sorted(self._balance):
                value = self._balance[currency][row]
                if self._seen[currency][row] and value != 0.0:
                    money[currency] = value
        return {"money": money, "goods": self.goods_held(agent)}

    def goods_of(self, agent: AgentId) -> Dict[GoodId, Dict[TileId, float]]:
        """What the agent holds, good to tile to quantity: a copy, in no stated order, and it may hold zeros.
        A caller that adds quantities sums them exactly."""
        slots = self._agent_slots.get(agent)
        if not slots:
            return {}
        held: Dict[GoodId, Dict[TileId, float]] = {}
        quantities, keys = self._qty, self._slot_key
        for slot in slots:
            _agent, good, tile = keys[slot]
            by_tile = held.get(good)
            if by_tile is None:
                by_tile = held[good] = {}
            by_tile[tile] = quantities[slot]
        return held

    def goods_held(self, agent: AgentId) -> Dict[GoodId, Dict[str, float]]:
        """What the agent holds of each good, by tile: goods and tiles in name order, nothing at zero."""
        goods = {}
        for good, by_tile in sorted(self.goods_of(agent).items()):
            tiles = {tile: value for tile, value in sorted(by_tile.items()) if value != 0.0}
            if tiles:
                goods[good] = tiles
        return goods

    def goods_totals(self) -> Dict[GoodId, float]:
        """Quantity held of each good by the agents (edge accounts excluded), goods in name order."""
        if not self._slot:
            return {}
        quantities = numpy.frombuffer(self._qty, dtype=numpy.float64).copy()
        rows = numpy.frombuffer(self._slot_row, dtype=numpy.int64).copy()
        goods = numpy.frombuffer(self._slot_good, dtype=numpy.int64).copy()
        edge = numpy.frombuffer(self._edge, dtype=numpy.uint8).copy()
        counted = (rows >= 0) & (quantities != 0.0)
        counted[counted] = edge[rows[counted]] == 0
        quantities, goods = quantities[counted], goods[counted]
        order = numpy.argsort(goods, kind="stable")
        quantities, goods = quantities[order], goods[order]
        starts = numpy.flatnonzero(numpy.diff(goods)) + 1 if len(goods) else numpy.zeros(0, dtype=numpy.int64)
        names = {number: good for good, number in self._good_number.items()}
        held = {}
        for group, numbers in zip(numpy.split(quantities, starts), numpy.split(goods, starts)):
            if len(group):
                held[names[int(numbers[0])]] = math.fsum(group.tolist())
        return dict(sorted(held.items()))

    def agents(self) -> List[AgentId]:
        return sorted(self._row)

    def holders_of(self, good: GoodId) -> List[AgentId]:
        """Agents (not edge accounts) holding some of the good."""
        keys, quantities = self._slot_key, self._qty
        return sorted({keys[slot][0] for slot in self._good_slots.get(good, ())
                       if quantities[slot] != 0.0 and not keys[slot][0].startswith(EDGE_PREFIX)})

    def money_supply(self, currency: CurrencyId) -> float:
        column = self._balance.get(currency)
        if column is None:
            return 0.0
        values = numpy.frombuffer(column, dtype=numpy.float64)
        counted = values[numpy.frombuffer(self._edge, dtype=numpy.uint8) == 0].tolist()
        del values
        return math.fsum(counted)

    def total(self, currency: CurrencyId) -> float:
        column = self._balance.get(currency)
        return math.fsum(column) if column is not None else 0.0

    def goods_total(self, good: GoodId) -> float:
        quantities = self._qty
        return math.fsum(quantities[slot] for slot in self._good_slots.get(good, ()))

    # ---- flows this year -----------------------------------------------------------------------

    def goods_flow(self, good: GoodId) -> Dict[str, float]:
        return dict(sorted(self._goods_by_purpose.get(good, {}).items()))

    def edge_volume(self, edge_id: AgentId, currency: CurrencyId) -> float:
        """Gross money in and out through an edge account this year."""
        both = self._edge_money.get((edge_id, currency))
        return both[0] if both else 0.0

    def edge_net(self, edge_id: AgentId, currency: CurrencyId) -> float:
        """Money the edge paid into the economy this year, less what it took out."""
        both = self._edge_money.get((edge_id, currency))
        return both[1] if both else 0.0

    def edge_goods_volume(self, edge_id: AgentId, good: GoodId) -> float:
        both = self._edge_goods.get((edge_id, good))
        return both[0] if both else 0.0

    def edge_goods_net(self, edge_id: AgentId, good: GoodId) -> float:
        both = self._edge_goods.get((edge_id, good))
        return both[1] if both else 0.0

    def edge_goods_agents(self) -> List[AgentId]:
        """Edge accounts that carried goods this year."""
        return sorted({agent for agent, _good in self._edge_goods})

    def currencies(self) -> List[CurrencyId]:
        return sorted(currency for currency, seen in self._seen.items() if any(seen))

    def supply_at_start(self, currency: CurrencyId) -> float:
        """The money supply (edge accounts excluded) when the year's flow records were last reset."""
        return self._supply_at_start.get(currency, 0.0)

    def edge_agents(self) -> List[AgentId]:
        """Edge accounts that carried money this year."""
        return sorted({agent for agent, _currency in self._edge_money})

    def start_year(self) -> None:
        """Reset the yearly flow records and note the supply; holdings carry."""
        self._supply_at_start = {currency: self.money_supply(currency) for currency in self.currencies()}
        self._goods_by_purpose = {}
        self._edge_money = {}
        self._edge_goods = {}

    def check_conservation(self, tolerance_share: float) -> ConservationReport:
        """Residual of each currency and good, as a share of everything ever booked in it."""
        money = {currency: _share(self.total(currency), gross) for currency, gross in sorted(self._gross_money.items())}
        goods = {good: _share(self.goods_total(good), gross) for good, gross in sorted(self._gross_goods.items())}
        breaches = tuple(["money %s: %.3g" % item for item in money.items() if item[1] > tolerance_share]
                         + ["goods %s: %.3g" % item for item in goods.items() if item[1] > tolerance_share])
        return ConservationReport(money, goods, breaches)
