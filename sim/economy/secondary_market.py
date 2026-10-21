"""The secondary market: holders sell claims they already hold to other agents at one price per claim.

Pure functions, like the market for new shares (share_market.py). A holder's ask is the lowest price it takes per
unit; a buyer's bid is the highest it pays, with the funds it brings. For each claim the price is where the units
offered at that price meet the units the bids can pay for (an auction that clears once a year), and a side that is
longer is served in proportion. A claim is worth to an agent the present value of what it is expected to pay, at the
rate that agent asks of a lender plus the premium for the issuer's risk (`present_value`).

Buyers spend one purse across the claims in turn (sorted by id), so what a buyer spends on one is not there for the
next. Nobody buys what it sells.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from sim.world import capital_market

from .types import AgentId

PRICE_ITERATIONS = 200       # bisection steps; the bracket is far narrower than a cent after them
EPSILON = 1e-12


@dataclass(frozen=True)
class Ask:
    seller: AgentId
    item: str                # the claim: a producer's equity, or a bond's contract id
    quantity: float          # units the seller holds for sale (a part of an equity, a face amount)
    reserve: float           # the lowest price per unit it accepts


@dataclass(frozen=True)
class Bid:
    buyer: AgentId
    item: str
    funds: float             # the most money it will spend on this claim
    limit: float             # the highest price per unit it pays


@dataclass(frozen=True)
class Trade:
    item: str
    seller: AgentId
    buyer: AgentId
    quantity: float
    price: float             # per unit; what the buyer pays is quantity times price


def present_value(coupon_per_unit: float, redemption_per_unit: float, years_left: Optional[float], rate: float) -> float:
    """What a claim paying `coupon_per_unit` a year, and `redemption_per_unit` after `years_left` years, is worth at
    `rate`. A claim with no end (`years_left` none or zero) is a perpetuity."""
    if years_left is None or years_left <= 0.0:
        return capital_market.perpetuity_value(coupon_per_unit, rate)
    growth = 1.0 + max(-0.99, rate)
    years = max(1, int(round(years_left)))
    coupons = sum(coupon_per_unit / growth ** year for year in range(1, years + 1))
    return coupons + redemption_per_unit / growth ** years


def _supply(asks: Sequence[Ask], price: float) -> float:
    return sum(ask.quantity for ask in asks if ask.reserve <= price)


def _demand(bids: Sequence[Bid], price: float) -> float:
    return sum(bid.funds / price for bid in bids if bid.limit >= price)


def clearing_price(asks: Sequence[Ask], bids: Sequence[Bid]) -> Optional[float]:
    """The lowest price at which the units offered cover the units the bids pay for; None when no bid reaches an ask."""
    asks = [ask for ask in asks if ask.quantity > 0.0]
    bids = [bid for bid in bids if bid.funds > 0.0 and bid.limit > 0.0]
    if not asks or not bids:
        return None
    low = max(min(ask.reserve for ask in asks), EPSILON)
    high = max(bid.limit for bid in bids)
    if low > high or _supply(asks, low) <= 0.0:
        return None
    if _supply(asks, low) >= _demand(bids, low):
        return low
    for _step in range(PRICE_ITERATIONS):
        middle = 0.5 * (low + high)
        if _supply(asks, middle) >= _demand(bids, middle):
            high = middle
        else:
            low = middle
    return high if _supply(asks, high) > 0.0 else None


def clear_item(asks: Sequence[Ask], bids: Sequence[Bid]) -> List[Trade]:
    """The trades in one claim at its clearing price. A holder does not bid on its own claim."""
    sellers = {ask.seller for ask in asks if ask.quantity > 0.0}
    bids = [bid for bid in bids if bid.buyer not in sellers]
    price = clearing_price(asks, bids)
    if price is None:
        return []
    selling = [ask for ask in sorted(asks, key=lambda each: (each.seller, each.reserve)) if ask.quantity > 0.0 and ask.reserve <= price]
    buying = [(bid.buyer, bid.funds / price) for bid in sorted(bids, key=lambda each: each.buyer) if bid.limit >= price]
    offered = sum(ask.quantity for ask in selling)
    wanted = sum(quantity for _buyer, quantity in buying)
    traded = min(offered, wanted)
    if traded <= 0.0:
        return []
    sell_part = traded / offered
    buy_part = traded / wanted
    trades = []
    for ask in selling:
        sold = ask.quantity * sell_part
        for buyer, quantity in buying:
            piece = sold * quantity * buy_part / traded
            if piece > EPSILON:
                trades.append(Trade(ask.item, ask.seller, buyer, piece, price))
    return trades


def clear(asks: Sequence[Ask], bids: Sequence[Bid]) -> List[Trade]:
    """Every claim's trades: claims in id order, each buyer's funds falling by what it spent on the ones before. A
    buyer's bids are caps on one purse: it has the most any of them names to spend over all."""
    funds: Dict[AgentId, float] = {}
    for bid in bids:
        funds[bid.buyer] = max(funds.get(bid.buyer, 0.0), bid.funds)
    trades: List[Trade] = []
    for item in sorted({ask.item for ask in asks}):
        item_bids = []
        for bid in sorted((each for each in bids if each.item == item), key=lambda each: each.buyer):
            money = min(bid.funds, funds.get(bid.buyer, 0.0))
            if money > 0.0:
                item_bids.append(Bid(bid.buyer, item, money, bid.limit))
        done = clear_item([ask for ask in asks if ask.item == item], item_bids)
        for trade in done:
            funds[trade.buyer] = funds.get(trade.buyer, 0.0) - trade.quantity * trade.price
        trades.extend(done)
    return trades
