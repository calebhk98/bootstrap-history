"""Turn a market's clearing result into postings on the book.

A clearing that records who bought from whom (`ClearingResult.pairing`) is settled pair by pair, each at its seller's
ask; any other result has its aggregate fills walked in order of (agent, tile) and matched greedily. When a payer cannot
cover what it owes, or a seller no longer holds what it sold, the affected pairs settle for the part that can be met: the
undelivered quantity stays with the seller and the unpaid money stays with the payer, and the gap is returned as a
`Shortfall`. A negative price (a waste someone is paid to take) reverses who pays.
"""
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Dict, List, Optional, Sequence, Tuple

from .accounts import Book, DeliveredMove
from .settlement_limits import CANNOT_PAY, limit_by_purse, limit_by_stock, pair_fills
from .types import (EDGE_LEGACY, AgentId, ClearingResult, CurrencyId, Fill, LabourResult, Pairing, Transfer, is_edge)

@dataclass(frozen=True)
class Shortfall:
    agent: AgentId
    item: str                       # the good, or for labour the trade
    kind: str                       # CANNOT_PAY or CANNOT_DELIVER
    unsettled_quantity: float       # quantity (or hours) that did not change hands because of this agent
    unpaid_amount: float            # money owed and not paid; 0 for CANNOT_DELIVER


@dataclass
class Settlement:
    postings: List[object] = field(default_factory=list)       # the Transfers and GoodsMoves applied
    shortfalls: List[Shortfall] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.shortfalls

    def bought_by_buyer(self) -> Dict[AgentId, Tuple[float, float]]:
        """Of a goods settlement, buyer -> (units it received, money it paid net of any it was paid to take)."""
        bought: Dict[AgentId, Tuple[float, float]] = {}
        for posting in self.postings:
            if isinstance(posting, Transfer):
                for agent, sign in ((posting.payer, 1.0), (posting.payee, -1.0)):
                    units, money = bought.get(agent, (0.0, 0.0))
                    bought[agent] = (units, money + sign * posting.amount)
            else:
                units, money = bought.get(posting.receiver, (0.0, 0.0))
                bought[posting.receiver] = (units + posting.quantity, money)
        return bought


def settle_goods(book: Book, result: ClearingResult) -> Settlement:
    return _settle(book, result.fills, result.currency, result.good,
                   "sale of %s" % result.good, delivers_goods=True, pairing=result.pairing)


def settle_labour(book: Book, result: LabourResult) -> Settlement:
    """Wages employer to worker; hours not paid for are reported as unsettled."""
    return _settle(book, result.fills, result.currency, result.trade,
                   "wages for %s" % result.trade, delivers_goods=False)


def book_legacy(book: Book, agent: AgentId, currency: CurrencyId, amount: float, purpose: str):
    """A one-sided engine posting: positive pays the agent from the legacy edge, negative takes from the agent."""
    if amount == 0.0:
        return None
    transfer = (Transfer(EDGE_LEGACY, agent, currency, amount, purpose) if amount > 0.0
                else Transfer(agent, EDGE_LEGACY, currency, -amount, purpose))
    book.transfer(transfer)
    return transfer


def _settle(book: Book, fills: Sequence[Fill], currency: CurrencyId, item: str,
            purpose: str, delivers_goods: bool, pairing: Optional[Pairing] = None) -> Settlement:
    """Each pair of a buyer and a seller moves money at the seller's own price: a seller receives its ask and a buyer pays
    the asks of the sellers it bought from. A clearing that says who bought from whom (`pairing`) settles those pairs; any
    other is paired by walking buyers and sellers in order of (agent, tile), each seller's fill price being its ask."""
    if pairing is None:
        pairing = _paired_by_walking(fills)
    settlement = Settlement()
    if not pairing.quantity:
        return settlement
    buyer_keys = [pairing.buyers[index] for index in pairing.buyer_index]
    seller_keys = [pairing.sellers[index] for index in pairing.seller_index]
    amounts = list(pairing.quantity)
    unsettled: Dict[Tuple[AgentId, str], float] = {}
    remaining_stock = {key: book.stock(key[0], item, key[1]) for key in set(seller_keys)}
    if delivers_goods:
        limit_by_stock(remaining_stock, seller_keys, amounts, unsettled)
    pair_prices = [pairing.asks[index] for index in pairing.seller_index]
    payers = [buyer[0] if price >= 0.0 else seller[0] for buyer, seller, price in zip(buyer_keys, seller_keys, pair_prices)]
    payees = [seller[0] if price >= 0.0 else buyer[0] for buyer, seller, price in zip(buyer_keys, seller_keys, pair_prices)]
    unit_prices = [abs(price) for price in pair_prices]
    remaining_cash = {payer: book.balance(payer, currency) for payer in set(payers)}
    unpaid = limit_by_purse(remaining_cash, payers, amounts, unit_prices, unsettled)
    transfers, moves = [], []
    edge_payers = {payer for payer in remaining_cash if is_edge(payer)}
    edge_sellers = {key for key in remaining_stock if is_edge(key[0])}
    for buyer_key, seller_key, amount, payer, payee, unit_price in zip(buyer_keys, seller_keys, amounts, payers, payees,
                                                                       unit_prices):
        if amount <= 0.0:
            continue
        if delivers_goods:
            if seller_key not in edge_sellers:
                amount = min(amount, remaining_stock[seller_key])
                remaining_stock[seller_key] -= amount
            moves.append(DeliveredMove(seller_key[0], buyer_key[0], item, seller_key[1], amount, purpose, buyer_key[1]))
        money = amount * unit_price
        if payer not in edge_payers:
            money = min(money, remaining_cash[payer])
            remaining_cash[payer] -= money
        if money > 0.0:
            transfers.append(Transfer(payer, payee, currency, money, purpose))
    book.post(transfers, moves)
    settlement.postings = transfers + moves
    settlement.shortfalls.extend(_shortfalls(item, unsettled, unpaid))
    return settlement


def _paired_by_walking(fills: Sequence[Fill]) -> Pairing:
    """Buyers and sellers walked in order of (agent, tile) and matched until one side runs out; a seller's ask is its
    fill price."""
    order = attrgetter("agent", "tile")
    buys = sorted((fill for fill in fills if fill.side == "buy" and fill.quantity > 0.0), key=order)
    sells = sorted((fill for fill in fills if fill.side == "sell" and fill.quantity > 0.0), key=order)
    buyer_index, seller_index, quantity = pair_fills(buys, sells)
    return Pairing(tuple((fill.agent, fill.tile) for fill in buys), tuple((fill.agent, fill.tile) for fill in sells),
                   tuple(fill.price for fill in sells), tuple(buyer_index), tuple(seller_index), tuple(quantity))


def _shortfalls(item: str, unsettled: Dict[Tuple[AgentId, str], float], unpaid: Dict[AgentId, float]) -> List[Shortfall]:
    records = []
    for (agent, kind), lost in sorted(unsettled.items()):
        records.append(Shortfall(agent, item, kind, lost, unpaid.get(agent, 0.0) if kind == CANNOT_PAY else 0.0))
    return records
