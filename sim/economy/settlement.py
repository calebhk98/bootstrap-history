"""Turn a market's clearing result into postings on the book.

Fills are aggregate per agent. Every buyer is matched with every seller in proportion to their
quantities, so each pays each seller its share and each seller's goods go to each buyer in the same
shares. When a payer cannot cover what it owes, or a seller no longer holds what it sold, the
affected pairs settle for the part that can be met: the undelivered quantity stays with the seller
and the unpaid money stays with the payer, and the gap is returned as a `Shortfall`. A negative
clearing price (a waste someone is paid to take) reverses who pays.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from .accounts import Book, DeliveredMove
from .types import (EDGE_LEGACY, AgentId, ClearingResult, CurrencyId, Fill, LabourResult, Transfer, is_edge)

CANNOT_PAY = "cannot_pay"
CANNOT_DELIVER = "cannot_deliver"


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
    buys = [fill for fill in fills if fill.side == "buy" and fill.quantity > 0.0]
    sells = [fill for fill in fills if fill.side == "sell" and fill.quantity > 0.0]
    settlement = Settlement()
    total_bought = sum(fill.quantity for fill in buys)
    total_sold = sum(fill.quantity for fill in sells)
    matched = min(total_bought, total_sold)
    if matched <= 0.0:
        return settlement
    quantity = {}
    for buy_index, buy in enumerate(buys):
        buy_share = buy.quantity / total_bought
        for sell_index, sell in enumerate(sells):
            quantity[(buy_index, sell_index)] = buy_share * (sell.quantity / total_sold) * matched
    unsettled: Dict[Tuple[AgentId, str], float] = {}
    if delivers_goods:
        _limit_by_stock(book, item, sells, buys, quantity, unsettled)
    payer_of = (lambda buy, sell: buy.agent) if price >= 0.0 else (lambda buy, sell: sell.agent)
    payee_of = (lambda buy, sell: sell.agent) if price >= 0.0 else (lambda buy, sell: buy.agent)
    unpaid = _limit_by_purse(book, currency, buys, sells, quantity, abs(price), payer_of, unsettled)
    transfers, moves = [], []
    remaining_cash = {agent: book.balance(agent, currency) for agent in {payer_of(b, s) for b in buys for s in sells}}
    remaining_stock = {(sell.agent, sell.tile): book.stock(sell.agent, item, sell.tile) for sell in sells}
    for (buy_index, sell_index), amount in sorted(quantity.items()):
        buy, sell = buys[buy_index], sells[sell_index]
        if amount <= 0.0:
            continue
        if delivers_goods:
            key = (sell.agent, sell.tile)
            if not is_edge(sell.agent):
                amount = min(amount, remaining_stock[key])
                remaining_stock[key] -= amount
            moves.append(DeliveredMove(sell.agent, buy.agent, item, sell.tile, amount, purpose, buy.tile))
        payer = payer_of(buy, sell)
        money = amount * abs(price)
        if not is_edge(payer):
            money = min(money, remaining_cash[payer])
            remaining_cash[payer] -= money
        if money > 0.0:
            transfers.append(Transfer(payer, payee_of(buy, sell), currency, money, purpose))
    book.post(transfers, moves)
    settlement.postings = transfers + moves
    settlement.shortfalls.extend(_shortfalls(item, unsettled, unpaid))
    return settlement


def _limit_by_stock(book, good, sells, buys, quantity, unsettled) -> None:
    """Scale each seller's pairs down to what it holds on its tile."""
    held = {}
    for sell_index, sell in enumerate(sells):
        key = (sell.agent, sell.tile)
        if key not in held:
            held[key] = book.stock(sell.agent, good, sell.tile)
    indices_by_key: Dict[Tuple[AgentId, str], List[int]] = {}
    for sell_index, sell in enumerate(sells):
        indices_by_key.setdefault((sell.agent, sell.tile), []).append(sell_index)
    for key, indices in sorted(indices_by_key.items()):
        if is_edge(key[0]):
            continue
        pairs = [(buy_index, sell_index) for sell_index in indices for buy_index in range(len(buys))]
        wanted = sum(quantity[pair] for pair in pairs)
        if wanted > held[key]:
            scale = max(held[key], 0.0) / wanted
            for pair in pairs:
                quantity[pair] *= scale
            unsettled[(key[0], CANNOT_DELIVER)] = unsettled.get((key[0], CANNOT_DELIVER), 0.0) + wanted * (1.0 - scale)


def _limit_by_purse(book, currency, buys, sells, quantity, unit_price, payer_of, unsettled):
    """Scale each payer's pairs down to what it can pay; returns the money left unpaid per payer."""
    pairs_by_payer: Dict[AgentId, List[Tuple[int, int]]] = {}
    for buy_index, buy in enumerate(buys):
        for sell_index, sell in enumerate(sells):
            pairs_by_payer.setdefault(payer_of(buy, sell), []).append((buy_index, sell_index))
    unpaid: Dict[AgentId, float] = {}
    for payer, pairs in sorted(pairs_by_payer.items()):
        if is_edge(payer):
            continue
        owed = sum(quantity[pair] for pair in pairs) * unit_price
        balance = book.balance(payer, currency)
        if owed > balance:
            scale = max(balance, 0.0) / owed
            lost = 0.0
            for pair in pairs:
                lost += quantity[pair] * (1.0 - scale)
                quantity[pair] *= scale
            unsettled[(payer, CANNOT_PAY)] = unsettled.get((payer, CANNOT_PAY), 0.0) + lost
            unpaid[payer] = owed - max(balance, 0.0)
    return unpaid


def _shortfalls(item: str, unsettled: Dict[Tuple[AgentId, str], float], unpaid: Dict[AgentId, float]) -> List[Shortfall]:
    records = []
    for (agent, kind), lost in sorted(unsettled.items()):
        records.append(Shortfall(agent, item, kind, lost, unpaid.get(agent, 0.0) if kind == CANNOT_PAY else 0.0))
    return records
