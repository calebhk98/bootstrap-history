"""A household rationed on a good spends what it did not spend on the goods that meet the same need, then on its
other needs, before anything is saved. A rationed Eurace household sends the leftover to a second choice by the
same logit; the leftover going on to other needs is this project's extension (in Eurace it stays in the payment
account). The functions here are the rules; goods_respend_year.py runs them on a year's markets.
"""
import math
from dataclasses import replace
from typing import Dict, List, Mapping, Optional, Sequence

from sim.constants import declare
from sim.world import need_basket

from .goods_market import quantity_at
from .types import Bid, Offer

RESPEND_PRIORITY = 1       # the leftover is surplus spending: it queues behind the first-round bids
RESPEND_NEGLIGIBLE_ROUND_SHARE = declare(
    "RESPEND_NEGLIGIBLE_ROUND_SHARE", 1e-6, kind="temporary_heuristic",
    unit="share of the money the year's respend rounds have paid", source=None, confidence="D",
    why="A respend round that pays less than this share of what the year's rounds have paid so far is the last: the "
        "rounds after the first few pay a falling fraction of the round before, mostly in one market whose sellers "
        "sell a little more each round, and running them to the bound costs a large part of a big economy's year. "
        "The money left is kept by the cohort, as money no offered good takes already is.",
    retire="Complaints/497: the respend rounds' limit computed in closed form, or bids that fill in one round")


def last_round_negligible(paid_this_round: float, paid_so_far: float) -> bool:
    """Whether a respend round that paid `paid_this_round` is the last, given `paid_so_far` by all the year's respend
    rounds including this one: it paid nothing, or a negligible share of that (RESPEND_NEGLIGIBLE_ROUND_SHARE)."""
    return paid_this_round <= 0.0 or paid_this_round < RESPEND_NEGLIGIBLE_ROUND_SHARE * paid_so_far


def rationed_money(bids: Sequence[Bid], taken: float, spent: float, price: float) -> float:
    """The money a buyer's bids in one market could still have used at `price`: the units it wanted there and did
    not get, at that price, and never more than the budgets it did not spend."""
    if len(bids) == 1:     # a sum of one number is the number
        budget = bids[0].budget
        wanted = quantity_at(bids[0], price) if price > 0.0 else 0.0
    else:
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


def priced_needs(basket: need_basket.Basket, asks: Mapping[str, float], cache: Optional[dict] = None
                 ) -> Dict[str, need_basket.PricedNeed]:
    """Each need of `basket` priced at the cheapest asks still offered (`asks`: good -> ask), those with a good offered.
    Households of one basket facing the same asks share the answer: with a `cache` (kept for a round or more) it is worked
    out once per basket and set of asks."""
    if cache is not None:
        goods = cache.get(id(basket))
        if goods is None:
            goods = cache[id(basket)] = (basket, tuple(sorted({good for spec in basket.needs for good, _effect in spec.goods})))
        key = (id(basket), tuple([asks.get(good) for good in goods[1]]))
        found = cache.get(key)
        if found is not None:
            return found
    exponent = 1.0 - basket.substitution
    by_need: Dict[str, need_basket.PricedNeed] = {}
    for spec in basket.needs:
        priced = need_basket.priced_need(spec, exponent, asks.get)
        if priced is not None:
            by_need[spec.need_id] = priced
    if cache is not None:
        cache[key] = by_need
    return by_need


def respend_bids(buyer: str, tile: str, basket: need_basket.Basket, rationed: Mapping[str, float],
                 asks: Mapping[str, float], area_of, cache: Optional[dict] = None) -> List[Bid]:
    """The bids that spend `rationed` (money by need id) on goods still offered (`asks`: good -> cheapest ask). A need's
    money goes to its own goods still offered, split by the household's choice rule (cost per need unit, the
    substitution of the basket); a need with none offered passes its money to the needs that have goods, by their
    budget weights. Money no offered good can serve is not bid."""
    by_need = priced_needs(basket, asks, cache)
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


def bid_units(bid: Bid) -> float:
    """The units a bid counts as asking for, at its own reference price: its floor and, with a budget and a reference price, its
    flexible part."""
    if bid.budget > 0.0 and bid.flexible_quantity > 0.0 and bid.reference_price > 0.0:
        return bid.floor_quantity + bid.flexible_quantity
    return bid.floor_quantity


def bids_adding_demand(earlier: Sequence[Bid], bids: Sequence[Bid]) -> List[Bid]:
    """The bids of a later round that add demand to a market, each cut to its new share: a buyer that already bid there in an
    earlier round wants the same units again, the part it was rationed on, so only the units beyond those the buyer has
    counted in the market add (a buyer new to the market counts in full, a bid wholly inside what was counted not at all). The
    one rule for what a market's demand is over its rounds (the stored bids, the wanted quantity and so the unmet quantity)."""
    counted: Dict[str, float] = {}
    for bid in earlier:
        counted[bid.buyer] = counted.get(bid.buyer, 0.0) + bid_units(bid)
    adding = []
    for bid in bids:
        units = bid_units(bid)
        fraction = max(0.0, units - counted.get(bid.buyer, 0.0)) / units if units > 0.0 else 0.0
        if fraction >= 1.0:
            adding.append(bid)
        elif fraction > 0.0:
            adding.append(replace(bid, flexible_quantity=bid.flexible_quantity * fraction, budget=bid.budget * fraction))
    return adding


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
