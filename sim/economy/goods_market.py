"""One market's clearing within a year: buyers' schedules against sellers' reservation prices.

Supply is a step function: a seller offers its whole quantity at any price at or above its
reservation. Demand is the sum of the buyers' `quantity_at` schedules, falling in price. The price is
where they meet. At the crossing the lowest-reservation sellers sell first and the marginal group is
filled pro rata. Buyers pay the clearing price; when supply falls short at that price they are served
by priority tier (lower first), pro rata within a tier.

Choices:
  * Prices are positive. A reservation at or below zero (a waste product) is treated as the lowest
    price the market considers, so such a seller sells whatever demand takes at that token price and
    the rest stays unsold; the price never clears below zero.
  * With no offers there is no trade and the price stays at the last price (0.0 if none), every
    floor unmet. With no demand nothing sells; the price is the last price if some seller would sell
    at it, else the lowest reservation.
"""
import math
from itertools import groupby
from operator import attrgetter, itemgetter
from typing import List, Optional, Sequence, Tuple

from sim.constants import declare

from .goods_market_demand import DemandSchedule
from .goods_market_fills import buyer_fills, seller_fills
from .goods_market_solve import solve_price
from .types import AreaId, Bid, ClearingResult, CurrencyId, GoodId, Offer

MINIMUM_PRICE_SHARE_OF_REFERENCE = declare(
    "MINIMUM_PRICE_SHARE_OF_REFERENCE", 1e-3, kind="temporary_heuristic",
    unit="share of the buyers' mean reference price",
    source=None, confidence="D",
    why="Prices clear on positive values, so a seller ready to pay to be rid of a good (reservation "
        "at or below zero) is placed at a token price instead. The token is a small share of the "
        "price scale buyers quote; waste disposal charged to the seller is not yet modelled.")
_BID_ORDER = attrgetter("priority", "buyer", "tile")
_OFFER_ORDER = attrgetter("reservation_price", "seller", "tile")
_PRIORITY = attrgetter("priority")
_FIRST = itemgetter(0)
CHEAP_PASSES_PER_BID = 10


def quantity_at(bid: Bid, price: float) -> float:
    """What the buyer wants at a price: floor plus a price-sensitive part, capped by what it can pay.
    At a price of zero or below the budget cap cannot be taken and the schedule's uncapped limit
    (floor plus flexible) is returned."""
    if bid.budget <= 0.0 or price > bid.maximum_price:
        return 0.0
    if price <= 0.0:
        return bid.floor_quantity + bid.flexible_quantity
    return _quantity(bid.floor_quantity, bid.flexible_quantity, bid.reference_price, bid.elasticity,
                     bid.budget, price)


def _quantity(floor, flexible, reference, elasticity, budget, price):
    wanted = floor
    if flexible > 0.0 and reference > 0.0:
        try:
            wanted += flexible * (price / reference) ** -elasticity
        except OverflowError:
            wanted = math.inf
    return min(wanted, budget / price)


def _empty(good, area, currency, price, bids, supply_at_price=0.0) -> ClearingResult:
    unmet = math.fsum(max(0.0, bid.floor_quantity) for bid in bids)
    return ClearingResult(good, area, currency, price, 0.0, 0.0, supply_at_price, unmet, ())


def _price_scale(bids: Sequence[Bid], last_price: Optional[float]) -> float:
    references = [bid.reference_price for bid in bids if bid.reference_price > 0.0]
    if references:
        return math.fsum(references) / len(references)
    return last_price if last_price and last_price > 0.0 else 1.0


def clear(bids: Sequence[Bid], offers: Sequence[Offer], good: GoodId, area: AreaId,
          currency: CurrencyId, last_price: Optional[float]) -> ClearingResult:
    """Clear one market for one year. Deterministic whatever the order of `bids` and `offers`."""
    bids = sorted(bids, key=_BID_ORDER)
    offers = sorted((offer for offer in offers if offer.quantity > 0.0), key=_OFFER_ORDER)
    held_price = last_price if last_price is not None else 0.0
    if not offers:
        return _empty(good, area, currency, held_price, bids)

    minimum_price = MINIMUM_PRICE_SHARE_OF_REFERENCE * _price_scale(bids, last_price)
    effective = [max(offer.reservation_price, minimum_price) for offer in offers]
    schedule = DemandSchedule(bids)

    demand_at_first = schedule.total_at(effective[0])
    if demand_at_first <= 0.0:
        lowest = offers[0].reservation_price
        price = held_price if last_price is not None and lowest <= last_price else lowest
        supply = math.fsum(offer.quantity for offer, reservation in zip(offers, effective)
                           if reservation <= max(price, minimum_price))
        return _empty(good, area, currency, price, bids, supply)

    levels, running = [], 0.0
    for reservation, group in groupby(zip(effective, offers), key=_FIRST):
        running += math.fsum(offer.quantity for _, offer in group)
        levels.append((reservation, running))
    price = solve_price(levels, schedule.total_at, demand_at_first,
                        schedule.uncapped_at if schedule.distinct_schedules() * CHEAP_PASSES_PER_BID <= len(bids) else None)

    eligible = [(reservation, offer) for reservation, offer in zip(effective, offers)
                if reservation <= price]
    supply = math.fsum(offer.quantity for _, offer in eligible)
    wants = schedule.each_at(price)
    wanted = math.fsum(wants)
    served = _ration(bids, wants, min(wanted, supply))
    traded = math.fsum(served)
    seller_quantities = _fill_sellers(eligible, traded)

    fills = buyer_fills(bids, served, good, area, price)
    fills.extend(seller_fills(seller_quantities, good, area, price))
    unmet = math.fsum([max(0.0, bid.floor_quantity - quantity) for bid, quantity in zip(bids, served)])
    return ClearingResult(good, area, currency, price, traded, wanted, supply, unmet, tuple(fills))


def _ration_buyers(bids: Sequence[Bid], price: float, available: float) -> List[Tuple[Bid, float]]:
    """Each buyer's served quantity at a price with `available` to share, in the order of `bids`."""
    served = _ration(bids, [quantity_at(bid, price) for bid in bids], available)
    return list(zip(bids, served))


def _ration(bids: Sequence[Bid], wants: List[float], available: float) -> List[float]:
    """Serve each priority tier in turn; a tier that cannot be served in full shares what is left pro rata."""
    result: List[float] = []
    remaining = available
    start = 0
    for _tier, tier_group in groupby(bids, key=_PRIORITY):
        end = start + sum(1 for _ in tier_group)
        tier_wants = wants[start:end]
        start = end
        total = math.fsum(tier_wants)
        if total <= 0.0:
            result.extend([0.0] * len(tier_wants))
        elif remaining >= total:
            result.extend(tier_wants)
            remaining -= total
        else:
            share = remaining / total
            result.extend([want * share for want in tier_wants])
            remaining = 0.0
    return result


def _fill_sellers(eligible: List[Tuple[float, Offer]], traded: float) -> List[Tuple[Offer, float]]:
    """Cheapest reservations sell fully; the group at the marginal reservation shares what is left pro rata."""
    result: List[Tuple[Offer, float]] = []
    remaining = traded
    for _reservation, group in groupby(eligible, key=_FIRST):
        offers = [offer for _, offer in group]
        total = math.fsum(offer.quantity for offer in offers)
        if remaining >= total:
            result.extend((offer, offer.quantity) for offer in offers)
            remaining -= total
        else:
            share = remaining / total if total > 0.0 else 0.0
            result.extend((offer, offer.quantity * share) for offer in offers)
            remaining = 0.0
    return result
