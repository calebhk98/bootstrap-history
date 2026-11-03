"""Pairing of a market's buyers with its sellers, and the scaling of pairs down to what purses and stocks allow.

Buyers and sellers are walked in order of (agent, tile) and matched greedily, so a market of many
buyers and a few sellers books about buyers plus sellers pairs rather than buyers times sellers. A pair
is three parallel lists: buyer index, seller index, quantity.
"""
from typing import Dict, List, Sequence, Tuple

from .types import AgentId, Fill, is_edge

CANNOT_PAY = "cannot_pay"
CANNOT_DELIVER = "cannot_deliver"

Pairs = Tuple[List[int], List[int], List[float]]


def pair_fills(buys: Sequence[Fill], sells: Sequence[Fill]) -> Pairs:
    """Match buyer quantity to seller quantity in order until one side runs out."""
    buyer_indices: List[int] = []
    seller_indices: List[int] = []
    amounts: List[float] = []
    if not buys or not sells:
        return buyer_indices, seller_indices, amounts
    buy_quantities = [fill.quantity for fill in buys]
    sell_quantities = [fill.quantity for fill in sells]
    buy_index = sell_index = 0
    buy_left, sell_left = buy_quantities[0], sell_quantities[0]
    buy_count, sell_count = len(buys), len(sells)
    while True:
        take = buy_left if buy_left < sell_left else sell_left
        buyer_indices.append(buy_index)
        seller_indices.append(sell_index)
        amounts.append(take)
        buy_left -= take
        sell_left -= take
        if buy_left <= 0.0:
            buy_index += 1
            if buy_index == buy_count:
                break
            buy_left = buy_quantities[buy_index]
        if sell_left <= 0.0:
            sell_index += 1
            if sell_index == sell_count:
                break
            sell_left = sell_quantities[sell_index]
    return buyer_indices, seller_indices, amounts


def limit_by_stock(held: Dict[Tuple[AgentId, str], float], keys: List[Tuple[AgentId, str]],
                   amounts: List[float], unsettled: Dict[Tuple[AgentId, str], float]) -> None:
    """Scale each seller's pairs (`keys`: the seller's agent and tile per pair) down to what it holds on its tile (`held`)."""
    scales = _scales(keys, amounts, held, [1.0] * len(amounts), lambda key: key[0])
    for key in sorted(scales):
        wanted, scale = scales[key]
        unsettled[(key[0], CANNOT_DELIVER)] = unsettled.get((key[0], CANNOT_DELIVER), 0.0) + wanted * (1.0 - scale)
    _apply(keys, amounts, scales)


def limit_by_purse(balances: Dict[AgentId, float], payers: List[AgentId], amounts: List[float], unit_prices: List[float],
                   unsettled: Dict[Tuple[AgentId, str], float]) -> Dict[AgentId, float]:
    """Scale each payer's pairs down to what it can pay, each pair at its own unit price (non-negative); returns the
    money left unpaid per payer."""
    scales = _scales(payers, amounts, balances, unit_prices, lambda payer: payer)
    unpaid: Dict[AgentId, float] = {}
    for payer in sorted(scales):
        owed, _scale = scales[payer]
        unpaid[payer] = owed - max(balances[payer], 0.0)
    lost = {payer: 0.0 for payer in scales}
    for payer, amount in zip(payers, amounts):
        if payer in scales:
            lost[payer] += amount * (1.0 - scales[payer][1])
    for payer in sorted(lost):
        unsettled[(payer, CANNOT_PAY)] = unsettled.get((payer, CANNOT_PAY), 0.0) + lost[payer]
    _apply(payers, amounts, scales)
    return unpaid


def _scales(keys, amounts: List[float], capacity: dict, unit_prices: List[float], agent_of) -> dict:
    """For each non-edge key whose pairs together cost more than its capacity: (what they cost, scale to fit)."""
    asked: dict = {}
    for key, amount, unit in zip(keys, amounts, unit_prices):
        asked[key] = asked.get(key, 0.0) + amount * unit
    scales = {}
    for key, total in asked.items():
        if total > capacity[key] and not is_edge(agent_of(key)):
            scales[key] = (total, max(capacity[key], 0.0) / total)
    return scales


def _apply(keys, amounts: List[float], scales: dict) -> None:
    if scales:
        for pair, key in enumerate(keys):
            if key in scales:
                amounts[pair] *= scales[key][1]
