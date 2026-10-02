"""Turn a market's clearing result into postings on the book.

Fills are aggregate per agent. Buyers and sellers are walked in order and matched greedily, so each
buyer pays the sellers its quantity falls on and each seller's goods go to those buyers. When a payer
cannot cover what it owes, or a seller no longer holds what it sold, the affected pairs settle for the part that can be met: the undelivered quantity stays with the seller
and the unpaid money stays with the payer, and the gap is returned as a `Shortfall`. A negative
clearing price (a waste someone is paid to take) reverses who pays.
"""
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Dict, List, Sequence, Tuple

from .accounts import Book, DeliveredMove
from .settlement_limits import CANNOT_DELIVER, CANNOT_PAY, limit_by_purse, limit_by_stock, pair_fills
from .types import (EDGE_LEGACY, AgentId, ClearingResult, CurrencyId, Fill, LabourResult, Transfer, is_edge)

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


def settle_goods(book: Book, result: ClearingResult) -> Settlement:
    return _settle(book, result.fills, result.price, result.currency, result.good,
                   "sale of %s" % result.good, delivers_goods=True)


def settle_labour(book: Book, result: LabourResult) -> Settlement:
    """Wages employer to worker; hours not paid for are reported as unsettled."""
    return _settle(book, result.fills, result.wage, result.currency, result.trade,
                   "wages for %s" % result.trade, delivers_goods=False)


def book_legacy(book: Book, agent: AgentId, currency: CurrencyId, amount: float, purpose: str):
    """A one-sided engine posting: positive pays the agent from the legacy edge, negative takes from the agent."""
    if amount == 0.0:
        return None
    transfer = (Transfer(EDGE_LEGACY, agent, currency, amount, purpose) if amount > 0.0
                else Transfer(agent, EDGE_LEGACY, currency, -amount, purpose))
    book.transfer(transfer)
    return transfer


def _settle(book: Book, fills: Sequence[Fill], price: float, currency: CurrencyId, item: str,
            purpose: str, delivers_goods: bool) -> Settlement:
    order = attrgetter("agent", "tile")
    buys = sorted((fill for fill in fills if fill.side == "buy" and fill.quantity > 0.0), key=order)
    sells = sorted((fill for fill in fills if fill.side == "sell" and fill.quantity > 0.0), key=order)
    settlement = Settlement()
    buyer_indices, seller_indices, amounts = pair_fills(buys, sells)
    if not amounts:
        return settlement
    unsettled: Dict[Tuple[AgentId, str], float] = {}
    remaining_stock = {(sell.agent, sell.tile): book.stock(sell.agent, item, sell.tile) for sell in sells}
    if delivers_goods:
        limit_by_stock(remaining_stock, sells, seller_indices, amounts, unsettled)
    buyers = [buys[index].agent for index in buyer_indices]
    sellers = [sells[index].agent for index in seller_indices]
    payers, payees = (buyers, sellers) if price >= 0.0 else (sellers, buyers)
    unit_price = abs(price)
    remaining_cash = {payer: book.balance(payer, currency) for payer in set(payers)}
    unpaid = limit_by_purse(remaining_cash, payers, amounts, unit_price, unsettled)
    transfers, moves = [], []
    edge_payers = {payer for payer in remaining_cash if is_edge(payer)}
    edge_sellers = {(sell.agent, sell.tile) for sell in sells if is_edge(sell.agent)}
    for buy_index, sell_index, amount, payer, payee in zip(buyer_indices, seller_indices, amounts, payers, payees):
        if amount <= 0.0:
            continue
        buy, sell = buys[buy_index], sells[sell_index]
        if delivers_goods:
            key = (sell.agent, sell.tile)
            if key not in edge_sellers:
                amount = min(amount, remaining_stock[key])
                remaining_stock[key] -= amount
            moves.append(DeliveredMove(sell.agent, buy.agent, item, sell.tile, amount, purpose, buy.tile))
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


def _shortfalls(item: str, unsettled: Dict[Tuple[AgentId, str], float], unpaid: Dict[AgentId, float]) -> List[Shortfall]:
    records = []
    for (agent, kind), lost in sorted(unsettled.items()):
        records.append(Shortfall(agent, item, kind, lost, unpaid.get(agent, 0.0) if kind == CANNOT_PAY else 0.0))
    return records
