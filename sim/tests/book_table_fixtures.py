"""Small hand-written book tables for the kernel tests: a few agents, balances, stock slots and postings, no game."""
import numpy

from sim.book_commit import create_slot
from sim.book_index import EMPTY, KeyedRows, pack_key
from sim.book_tables import (AGENTS, BALANCES, CURRENCIES, GOODS, GOODS_MOVE_POSTINGS, PLANS, TRANSFER_POSTINGS, Agents,
                             Balances, Currencies, EdgeGoods, EDGE_GOODS, Goods, GoodsMovePostings, GoodsTables, MoneyTables,
                             Plans, PurposeFlows, PURPOSE_FLOWS, Scratch, Stocks, STOCKS, TransferPostings)

STRIDE = 2      # two currencies: 0 and 1


def agents_table(*edge_flags: int) -> Agents:
    """One agent row per flag (1 for an edge account), none known yet, none holding a slot."""
    count = len(edge_flags)
    return AGENTS.table_of(Agents, is_edge=list(edge_flags), is_mint=[0] * count, is_external=[0] * count, kind=[0] * count,
                           known=[0] * count, first_slot=[-1] * count, last_slot=[-1] * count)


def balances_table(agents: int, amounts=None) -> Balances:
    """Balance cells for that many agents at STRIDE currencies each; `amounts` ({cell: amount}) are set and seen."""
    cells = agents * STRIDE
    table = BALANCES.table_of(Balances, amount=[0.0] * cells, seen=[0] * cells, edge_volume=[0.0] * cells,
                              edge_net=[0.0] * cells, edge_seen=[0] * cells)
    for cell, amount in (amounts or {}).items():
        table.amount[cell] = amount
        table.seen[cell] = 1
    return table


def currencies_table() -> Currencies:
    return CURRENCIES.table_of(Currencies, gross_posted=[0.0] * STRIDE, gross_seen=[0] * STRIDE,
                               supply_at_start=[0.0] * STRIDE, supply_seen=[0] * STRIDE)


def goods_table(goods: int = 2) -> Goods:
    return GOODS.table_of(Goods, gross_moved=[0.0] * goods, gross_seen=[0] * goods)


def money_tables(agents: Agents, balances: Balances) -> MoneyTables:
    return MoneyTables(agents, balances, STRIDE, currencies_table())


class StockBook:
    """The goods side of a book as bare tables: stock slots with their index, purpose flows, edge-goods rows."""

    def __init__(self, agents: Agents, goods: int = 2):
        self.agents = agents
        self.stocks = KeyedRows(STOCKS, Stocks, 8)
        self.flows = KeyedRows(PURPOSE_FLOWS, PurposeFlows, 8)
        self.edge_goods = KeyedRows(EDGE_GOODS, EdgeGoods, 8)
        self.goods = goods_table(goods)

    def hold(self, agent: int, good: int, tile: int, quantity: float) -> int:
        """Make the slot (agent, good, tile) holding the quantity; returns it."""
        slot = create_slot(self.stocks.table, self.stocks.index, self.agents, pack_key(agent, good, tile))
        self.stocks.table.quantity[slot] = quantity
        self.agents.known[agent] = 1
        return slot

    def quantity(self, agent: int, good: int, tile: int) -> float:
        slot = self.stocks.find(pack_key(agent, good, tile))
        return 0.0 if slot == EMPTY else float(self.stocks.table.quantity[slot])

    def tables(self) -> GoodsTables:
        return GoodsTables(self.agents, self.goods, self.stocks.table, self.stocks.index, self.flows.table, self.flows.index,
                           self.edge_goods.table, self.edge_goods.index)


def transfers_of(*rows) -> TransferPostings:
    """Transfer postings in one batch from (payer, payee, currency, amount) tuples; purpose 0, reference 0."""
    count = len(rows)
    columns = list(zip(*rows)) if rows else [[], [], [], []]
    return TRANSFER_POSTINGS.table_of(TransferPostings, payer=list(columns[0]), payee=list(columns[1]), currency=list(columns[2]),
                                      amount=list(columns[3]), purpose_code=[0] * count, purpose_reference=[0] * count,
                                      batch=[0] * count)


def moves_of(*rows) -> GoodsMovePostings:
    """Goods-move postings in one batch from (giver, receiver, good, tile, receiver_tile, quantity) tuples."""
    count = len(rows)
    columns = list(zip(*rows)) if rows else [[]] * 6
    return GOODS_MOVE_POSTINGS.table_of(
        GoodsMovePostings, giver=list(columns[0]), receiver=list(columns[1]), good=list(columns[2]), tile=list(columns[3]),
        receiver_tile=list(columns[4]), quantity=list(columns[5]), purpose_code=[0] * count, purpose_reference=[0] * count,
        batch=[0] * count)


def plan_and_index(rows: int):
    """An empty plan with room for that many rows and its own hash index."""
    from sim.book_index import index_size_for
    return PLANS.new_table(Plans, rows), numpy.full(index_size_for(rows), EMPTY, dtype=numpy.int64)


def scratch_for(money_rows: int, goods_rows: int) -> Scratch:
    return Scratch(*plan_and_index(2 * money_rows + 2), *plan_and_index(2 * goods_rows + 2))
