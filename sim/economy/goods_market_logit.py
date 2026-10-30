"""How a market's buyers are sent to its sellers: each buyer splits its demand over the sellers by the logit on their asks,
every seller sells at its own ask, and what a sold-out seller could not serve is sent again to the sellers still holding stock.

Follows Eurace@Unibi, Cons_Goods/Household_Consumer_Functions.c, Household_rank_and_buy_goods_1 and _2, and
Cons_Goods/Mall_functions.c, Mall_update_mall_stocks_sales_rationing_1 and _2:
  * round 1: a household weighs the sellers that have stock by exp(-intensity * log ask) and sends its weekly budget
    to one drawn by those weights (here its demand is split over all of them by the weights, the expectation of the
    draw: price_setting.choice_shares, the function sellers plan with);
  * a seller whose requests exceed its stock serves each by stock / requests (here lower priority tiers first, then
    pro rata: goods_market_ration.ration);
  * round 2: a household that was rationed does the same among the sellers still holding stock, with the budget it has
    left, and is rationed again if need be; there is no third round, so what is left is unmet.
Eurace's households have one budget and no price-sensitive quantity; here a buyer's quantity at an ask is its schedule's
(Bid, goods_market.quantity_at), so a request is the buyer's quantity at that ask times its share, and in round 2 it is
the quantity unmet, limited by the money unspent and by what the schedule still wants at the new ask. A buyer does not
choose a seller asking above its maximum price (Eurace has no such ceiling; the seller would only be sent buyers who
cannot take it).
"""
import math
from typing import Dict, List, Sequence, Tuple

from sim.book import ROUNDING_SHARE

from .goods_market_ration import ration
from .price_setting import choice_shares
from .types import Bid, Offer


class Allocation:
    """What the logit choice gave: per bid, (offer index, quantity) pairs; per offer, the quantity sold; the round-1
    requests in all (what buyers asked for at the asks before any seller ran out)."""

    def __init__(self, bought: List[List[Tuple[int, float]]], sold: List[float], requested: float):
        self.bought = bought
        self.sold = sold
        self.requested = requested


def _in_stock(left: Sequence[float], offers: Sequence[Offer]) -> List[bool]:
    return [remaining > ROUNDING_SHARE * offer.quantity for remaining, offer in zip(left, offers)]


def _shares(ceiling: float, asks: Sequence[float], stocked: Sequence[bool], memo: Dict[float, List[float]]) -> List[float]:
    """Each offer's share of a buyer whose maximum price is `ceiling`: zero for a seller out of stock or asking above it."""
    shares = memo.get(ceiling)
    if shares is None:
        open_offers = [index for index, ask in enumerate(asks) if stocked[index] and ask <= ceiling]
        shares = [0.0] * len(asks)
        for index, share in zip(open_offers, choice_shares([asks[index] for index in open_offers])):
            shares[index] = share
        memo[ceiling] = shares
    return shares


def allocate(bids: Sequence[Bid], offers: Sequence[Offer], asks: Sequence[float], each_at, maximums: Sequence[float]) -> Allocation:
    """Two rounds of choice among `offers` (asking `asks`) by `bids` (in tier order); `each_at(price)` gives every bid's
    quantity at a price, `maximums` every bid's maximum price."""
    count = len(bids)
    wants_at: Dict[float, List[float]] = {}
    for ask in asks:
        if ask not in wants_at:
            wants_at[ask] = each_at(ask)
    left = [offer.quantity for offer in offers]
    bought: List[List[Tuple[int, float]]] = [[] for _ in range(count)]
    taken = [0.0] * count           # quantity each bid has been served so far
    unmet = [0.0] * count           # quantity it asked for in round 1 and was not served
    unmet_money = [0.0] * count     # what that quantity would have cost at the asks it was sent to

    stocked = _in_stock(left, offers)
    memo: Dict[float, List[float]] = {}
    first = {index: [_shares(maximums[i], asks, stocked, memo)[index] * wants_at[ask][i] for i in range(count)]
             for index, ask in enumerate(asks) if stocked[index]}
    requested = math.fsum(math.fsum(requests) for requests in first.values())
    for index, requests in first.items():
        for i, shortfall in _serve(index, requests, bids, left, bought, taken):
            unmet[i] += shortfall
            unmet_money[i] += shortfall * asks[index]

    stocked = _in_stock(left, offers)
    if any(stocked) and any(amount > 0.0 for amount in unmet):
        memo = {}
        second = {index: [_shares(maximums[i], asks, stocked, memo)[index]
                          * min(unmet[i], unmet_money[i] / ask, max(0.0, wants_at[ask][i] - taken[i])) if unmet[i] > 0.0 else 0.0
                          for i in range(count)]
                  for index, ask in enumerate(asks) if stocked[index]}
        for index, requests in second.items():
            _serve(index, requests, bids, left, bought, taken)
    return Allocation(bought, [offer.quantity - remaining for offer, remaining in zip(offers, left)], requested)


def _serve(index: int, requests: List[float], bids: Sequence[Bid], left: List[float],
           bought: List[List[Tuple[int, float]]], taken: List[float]) -> List[Tuple[int, float]]:
    """One offer meets the requests sent to it (Mall_update_mall_stocks_sales_rationing_1): all are served if it holds
    enough, else tiers in turn. Returns (bid index, quantity not served) for each bid left short."""
    total = math.fsum(requests)
    if total <= 0.0:
        return []
    if total <= left[index]:
        served, left[index] = requests, left[index] - total
    else:
        served, left[index] = ration(bids, requests, left[index]), 0.0
    short = []
    for i, (request, quantity) in enumerate(zip(requests, served)):
        if quantity > 0.0:
            bought[i].append((index, quantity))
            taken[i] += quantity
        if request - quantity > ROUNDING_SHARE * request:
            short.append((i, request - quantity))
    return short
