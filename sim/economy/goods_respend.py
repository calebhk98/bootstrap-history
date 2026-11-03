"""A household rationed on a good spends what it did not spend on the goods that meet the same need, then on its
other needs, before anything is saved. A rationed Eurace household sends the leftover to a second choice by the
same logit; the leftover going on to other needs is this project's extension (in Eurace it stays in the payment
account). The functions here are the rules; goods_respend_year.py runs them on a year's markets.
"""
import math
from typing import Dict, List, Mapping, Sequence

from sim.world import need_basket

from .goods_market import quantity_at
from .types import Bid, Offer

RESPEND_PRIORITY = 1       # the leftover is surplus spending: it queues behind the first-round bids


def rationed_money(bids: Sequence[Bid], taken: float, spent: float, price: float) -> float:
    """The money a buyer's bids in one market could still have used at `price`: the units it wanted there and did
    not get, at that price, and never more than the budgets it did not spend."""
    budget = math.fsum(bid.budget for bid in bids)
    wanted = math.fsum(quantity_at(bid, price) for bid in bids) if price > 0.0 else 0.0
    return max(0.0, min(budget - spent, (wanted - taken) * price))


def need_of_good(basket: need_basket.Basket) -> Dict[str, str]:
    """The need each good serves (the first, for a good that serves several)."""
    served: Dict[str, str] = {}
    for spec in basket.needs:
        for good, _effect in spec.goods:
            served.setdefault(good, spec.need_id)
    return served


def respend_bids(buyer: str, tile: str, basket: need_basket.Basket, rationed: Mapping[str, float],
                 asks: Mapping[str, float], area_of) -> List[Bid]:
    """The bids that spend `rationed` (money by need id) on goods still offered (`asks`: good -> cheapest ask). A need's
    money goes to its own goods still offered, split by the household's choice rule (cost per need unit, the
    substitution of the basket); a need with none offered passes its money to the needs that have goods, by their
    budget weights. Money no offered good can serve is not bid."""
    exponent = 1.0 - basket.substitution
    by_need: Dict[str, need_basket.PricedNeed] = {}
    for spec in basket.needs:
        priced = need_basket.priced_need(spec, exponent, asks.get)
        if priced is not None:
            by_need[spec.need_id] = priced
    money = {need_id: amount for need_id, amount in rationed.items() if amount > 0.0 and need_id in by_need}
    passed = math.fsum(amount for need_id, amount in rationed.items() if amount > 0.0 and need_id not in by_need)
    weight_total = math.fsum(priced.spec.budget_weight for priced in by_need.values())
    if passed > 0.0 and weight_total > 0.0:
        for need_id, priced in by_need.items():
            money[need_id] = money.get(need_id, 0.0) + passed * priced.spec.budget_weight / weight_total
    spend: Dict[str, float] = {}
    ceiling: Dict[str, float] = {}
    for need_id, amount in money.items():
        priced = by_need[need_id]
        for (good, _price, _effect, share), cap in zip(priced.goods, priced.ceilings or (math.inf,) * len(priced.goods)):
            if share * amount > 0.0:
                spend[good] = spend.get(good, 0.0) + amount * share
                ceiling[good] = min(ceiling.get(good, math.inf), cap)
    return [Bid(buyer, good, area_of(good), tile, 0.0, amount / asks[good], asks[good], basket.substitution, amount,
                RESPEND_PRIORITY, maximum_price=ceiling[good])
            for good, amount in sorted(spend.items())]


def bids_adding_demand(earlier: Sequence[Bid], bids: Sequence[Bid]) -> List[Bid]:
    """The bids of a later round that add demand to a market: a buyer that already bid there in an earlier round wants
    the same units again, the part it was rationed on, so only a buyer new to the market counts in full. The one rule
    for what a market's demand is over its rounds (the stored bids, the wanted quantity and so the unmet quantity)."""
    bidding = {bid.buyer for bid in earlier}
    return [bid for bid in bids if bid.buyer not in bidding]


def offers_left(offers: Sequence[Offer], sold: Mapping[tuple, float]) -> List[Offer]:
    """The offers with what sold (by (seller, tile)) taken off; offers with nothing left are dropped."""
    left = []
    remaining = dict(sold)
    for offer in offers:
        key = (offer.seller, offer.tile)
        taken = min(offer.quantity, remaining.get(key, 0.0))
        remaining[key] = remaining.get(key, 0.0) - taken
        if offer.quantity - taken > 0.0:
            left.append(Offer(offer.seller, offer.good, offer.area, offer.tile, offer.quantity - taken,
                              offer.reservation_price))
    return left
