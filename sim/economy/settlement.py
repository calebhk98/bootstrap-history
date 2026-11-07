"""Turn a market's clearing result into postings on the book.

A clearing that records who bought from whom (`ClearingResult.pairing`) is settled pair by pair, each at its seller's
ask; a labour result has its aggregate fills walked in order of (agent, tile) and matched greedily. When a payer cannot
cover what it owes, or a seller no longer holds what it sold, the affected pairs settle for the part that can be met: the
undelivered quantity stays with the seller and the unpaid money stays with the payer. A negative price (a waste someone is
paid to take) reverses who pays.

The pairs are packed once, settled by `settlement_kernel.settle_pairs`, and posted summed per agent
(`Book.post_settled`); the Transfers and GoodsMoves of the old per-pair settlement are rebuilt only when asked
(`Settlement.postings`).
"""
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

import numpy

from sim.book import Book, DeliveredMove
from .settlement_kernel import settle_pairs
from .settlement_limits import pair_fills
from .types import (EDGE_MINT, AgentId, ClearingResult, CurrencyId, Fill, LabourResult, Pairing, Transfer, is_edge,
                    is_external_edge)

NO_ACCOUNTS: FrozenSet[AgentId] = frozenset()


@dataclass
class Settlement:
    """What a market's settlement did, summed: per agent the money it paid and received and the goods it got and gave, per
    (agent, tile) key the goods delivered to the mint, and per pair the goods and money moved. `imports` and `exports` are
    the year ledger's foreign-money figures by agent (`YearLedger._note_foreign`)."""
    item: str = ""
    purpose: str = ""
    currency: CurrencyId = ""
    agents: List[AgentId] = field(default_factory=list)
    paid: List[float] = field(default_factory=list)
    received: List[float] = field(default_factory=list)
    goods_in: List[float] = field(default_factory=list)
    goods_out: List[float] = field(default_factory=list)
    buyer_net: List[float] = field(default_factory=list)       # money paid as a buyer, net of money paid to take
    got_goods: List[bool] = field(default_factory=list)
    paid_as_buyer: List[bool] = field(default_factory=list)
    imports: List[float] = field(default_factory=list)
    exports: List[float] = field(default_factory=list)
    keys: List[Tuple[AgentId, str]] = field(default_factory=list)
    key_to_mint: List[float] = field(default_factory=list)
    delivered: float = 0.0                                     # goods moved
    pairs: Optional[Tuple] = None      # (pairing, buyer_index, seller_index, receipt_key, payer, goods, money) for `postings`

    @property
    def postings(self) -> List[object]:
        """The Transfers and GoodsMoves applied, one of each per pair that moved something."""
        if self.pairs is None:
            return []
        pairing, buyer_index, seller_index, receipt_key, payer, goods, money = self.pairs
        transfers, moves = [], []
        for pair in range(len(goods)):
            buyer = pairing.buyers[buyer_index[pair]]
            seller = pairing.sellers[seller_index[pair]]
            if goods[pair] > 0.0:
                moves.append(DeliveredMove(seller[0], buyer[0], self.item, seller[1], float(goods[pair]), self.purpose,
                                           self.keys[receipt_key[pair]][1]))
            if money[pair] > 0.0:
                paying = self.agents[payer[pair]]
                transfers.append(Transfer(paying, seller[0] if paying == buyer[0] else buyer[0], self.currency,
                                          float(money[pair]), self.purpose))
        return transfers + moves

    @property
    def buyer_money(self) -> Dict[AgentId, float]:
        return {agent: net for agent, net, seen in zip(self.agents, self.buyer_net, self.paid_as_buyer) if seen}

    @property
    def paid_to(self) -> Dict[AgentId, float]:
        """Agent -> money it received (only those that received any)."""
        return {agent: amount for agent, amount in zip(self.agents, self.received) if amount > 0.0}

    @property
    def paid_by(self) -> Dict[AgentId, float]:
        """Agent -> money it paid (only those that paid any)."""
        return {agent: amount for agent, amount in zip(self.agents, self.paid) if amount > 0.0}

    def bought_by_buyer(self) -> Dict[AgentId, Tuple[float, float]]:
        """Of a goods settlement, buyer -> (units it received, money it paid net of any it was paid to take). Only the buyer
        side of each sale counts: money a buyer receives as a seller in the same market is not netted out."""
        bought: Dict[AgentId, Tuple[float, float]] = {}
        for agent, units, got, net, seen in zip(self.agents, self.goods_in, self.got_goods, self.buyer_net,
                                                self.paid_as_buyer):
            if got or seen:
                bought[agent] = (units, net if seen else 0.0)
        return bought


def settle_goods(book: Book, result: ClearingResult, import_accounts: FrozenSet[AgentId] = NO_ACCOUNTS,
                 export_accounts: FrozenSet[AgentId] = NO_ACCOUNTS) -> Settlement:
    """The result's pairing settled on the book. The accounts are the year ledger's customs accounts
    (`YearLedger.import_accounts`, `export_accounts`), which decide the settlement's import and export figures."""
    return _settle(book, result.fills, result.currency, result.good,
                   "sale of %s" % result.good, delivers_goods=True, pairing=result.pairing,
                   import_accounts=import_accounts, export_accounts=export_accounts)


def settle_labour(book: Book, result: LabourResult) -> Settlement:
    """Wages employer to worker; hours the employer cannot pay for are not settled."""
    return _settle(book, result.fills, result.currency, result.trade,
                   "wages for %s" % result.trade, delivers_goods=False)


class _Keys:
    """The (agent, tile) keys and the agents of one settlement, numbered in order of first use."""

    def __init__(self):
        self.keys: List[Tuple[AgentId, str]] = []
        self.number: Dict[Tuple[AgentId, str], int] = {}
        self.agents: List[AgentId] = []
        self.agent_number: Dict[AgentId, int] = {}

    def add(self, key: Tuple[AgentId, str]) -> int:
        number = self.number.get(key)
        if number is None:
            number = self.number[key] = len(self.keys)
            self.keys.append(key)
            if key[0] not in self.agent_number:
                self.agent_number[key[0]] = len(self.agents)
                self.agents.append(key[0])
        return number


def _settle(book: Book, fills: Sequence[Fill], currency: CurrencyId, item: str,
            purpose: str, delivers_goods: bool, pairing: Optional[Pairing] = None,
            import_accounts: FrozenSet[AgentId] = NO_ACCOUNTS, export_accounts: FrozenSet[AgentId] = NO_ACCOUNTS
            ) -> Settlement:
    """Each pair of a buyer and a seller moves money at the seller's own price: a seller receives its ask and a buyer pays
    the asks of the sellers it bought from. A clearing that says who bought from whom (`pairing`) settles those pairs; any
    other is paired by walking buyers and sellers in order of (agent, tile), each seller's fill price being its ask."""
    if pairing is None:
        pairing = _paired_by_walking(fills)
    settlement = Settlement(item=item, purpose=purpose, currency=currency)
    count = len(pairing.quantity)
    if not count:
        return settlement
    buyer_index = numpy.fromiter(pairing.buyer_index, dtype=numpy.int64, count=count)
    seller_index = numpy.fromiter(pairing.seller_index, dtype=numpy.int64, count=count)
    quantity = numpy.fromiter(pairing.quantity, dtype=float, count=count)
    asks = numpy.fromiter(pairing.asks, dtype=float, count=len(pairing.asks))
    table = _Keys()
    used_buyers = sorted(set(pairing.buyer_index))
    bid_key = numpy.full(len(pairing.buyers), -1, dtype=numpy.int64)
    for index in used_buyers:
        bid_key[index] = table.add(pairing.buyers[index])
    offer_key = numpy.full(len(pairing.sellers), -1, dtype=numpy.int64)
    for index in sorted(set(pairing.seller_index)):
        offer_key[index] = table.add(pairing.sellers[index])
    buyer_key, seller_key = bid_key[buyer_index], offer_key[seller_index]
    receipt_key = buyer_key
    if delivers_goods and not all(pairing.buyers[index][1] for index in used_buyers):
        # a buyer with no tile takes delivery where the seller holds the goods
        receipt_key = numpy.array([buyer_key[pair] if pairing.buyers[buyer_index[pair]][1] else
                                   table.add((pairing.buyers[buyer_index[pair]][0], pairing.sellers[seller_index[pair]][1]))
                                   for pair in range(count)], dtype=numpy.int64)
    keys, agents = table.keys, table.agents
    key_agent = numpy.array([table.agent_number[agent] for agent, _tile in keys], dtype=numpy.int64)
    key_stock = numpy.zeros(len(keys))
    if delivers_goods:
        for index in sorted(set(pairing.seller_index)):
            number = int(offer_key[index])
            key_stock[number] = book.stock(keys[number][0], item, keys[number][1])
    agent_cash = numpy.array([book.balance(agent, currency) for agent in agents])
    agent_edge = numpy.array([is_edge(agent) for agent in agents], dtype=numpy.bool_)
    agent_mint = numpy.array([agent == EDGE_MINT for agent in agents], dtype=numpy.bool_)
    agent_external = numpy.array([is_external_edge(agent) for agent in agents], dtype=numpy.bool_)
    agent_import = numpy.array([agent in import_accounts for agent in agents], dtype=numpy.bool_)
    agent_export = numpy.array([agent in export_accounts for agent in agents], dtype=numpy.bool_)
    (goods, money, payer, paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports, exports,
     key_given, key_taken, key_to_mint) = settle_pairs(
        receipt_key, seller_key, quantity, asks[seller_index], delivers_goods, delivers_goods, key_agent, key_stock,
        agent_cash, agent_edge, agent_mint, agent_external, agent_import, agent_export)
    book.post_settled(currency, purpose, item, agents, paid.tolist(), received.tolist(), keys, key_given.tolist(),
                      key_taken.tolist())
    settlement.agents, settlement.keys = agents, keys
    settlement.paid, settlement.received = paid.tolist(), received.tolist()
    settlement.goods_in, settlement.goods_out = goods_in.tolist(), goods_out.tolist()
    settlement.buyer_net, settlement.got_goods = buyer_net.tolist(), got_goods.tolist()
    settlement.paid_as_buyer = paid_as_buyer.tolist()
    settlement.imports, settlement.exports = imports.tolist(), exports.tolist()
    settlement.key_to_mint = key_to_mint.tolist()
    settlement.delivered = float(goods.sum())
    settlement.pairs = (pairing, buyer_index, seller_index, receipt_key, payer, goods, money)
    return settlement


def _paired_by_walking(fills: Sequence[Fill]) -> Pairing:
    """Labour only: goods results always carry a pairing. Buyers and sellers walked in order of (agent, tile) and matched
    until one side runs out; a seller's ask is its fill price."""
    order = attrgetter("agent", "tile")
    buys = sorted((fill for fill in fills if fill.side == "buy" and fill.quantity > 0.0), key=order)
    sells = sorted((fill for fill in fills if fill.side == "sell" and fill.quantity > 0.0), key=order)
    buyer_index, seller_index, quantity = pair_fills(buys, sells)
    return Pairing(tuple((fill.agent, fill.tile) for fill in buys), tuple((fill.agent, fill.tile) for fill in sells),
                   tuple(fill.price for fill in sells), tuple(buyer_index), tuple(seller_index), tuple(quantity))
