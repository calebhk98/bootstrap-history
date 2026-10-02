"""Straightforward clearing kept as the oracle for the optimised goods market: plain demand sums and
bisection in log price, as first written. Tests compare `clear` against it."""
import math
from itertools import groupby
from typing import Dict, List, Optional, Sequence, Tuple

from sim.economy.types import AreaId, Bid, ClearingResult, CurrencyId, Fill, GoodId, Offer

MINIMUM_PRICE_SHARE_OF_REFERENCE = 1e-3

BISECTION_STEPS = 200
BISECTION_RELATIVE_WIDTH = 1e-11


def quantity_at(bid: Bid, price: float) -> float:
    """What the buyer wants at a price: floor plus a price-sensitive part, capped by what it can pay.
    At a price of zero or below the budget cap cannot be taken and the schedule's uncapped limit
    (floor plus flexible) is returned."""
    if bid.budget <= 0.0:
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


def _demand_function(bids: Sequence[Bid]):
    rows = [(bid.floor_quantity, bid.flexible_quantity, bid.reference_price, bid.elasticity, bid.budget)
            for bid in bids if bid.budget > 0.0]

    def demand(price: float) -> float:
        return sum(_quantity(floor, flexible, reference, elasticity, budget, price)
                         for floor, flexible, reference, elasticity, budget in rows)
    return demand


def _empty(good, area, currency, price, bids, supply_at_price=0.0) -> ClearingResult:
    unmet = math.fsum(max(0.0, bid.floor_quantity) for bid in bids)
    return ClearingResult(good, area, currency, price, 0.0, 0.0, supply_at_price, unmet, ())


def _solve_price(levels: List[Tuple[float, float]], demand) -> float:
    """levels: (reservation, cumulative supply of sellers at or below it), ascending and positive.
    Returns the price where demand meets the step supply: at a reservation where demand falls
    inside the step up, or inside a flat stretch of supply by bisection."""
    for index, (reservation, supply) in enumerate(levels):
        if demand(reservation) <= supply:
            return reservation
        upper = levels[index + 1][0] if index + 1 < len(levels) else None
        if upper is not None and demand(upper) >= supply:
            continue
        high = upper if upper is not None else _find_upper(demand, reservation, supply)
        return _bisect(demand, reservation, high, supply)
    return levels[-1][0]


def _find_upper(demand, low: float, supply: float) -> float:
    high = low * 2.0
    for _ in range(2000):
        if demand(high) < supply:
            return high
        high *= 2.0
    return high


def _bisect(demand, low: float, high: float, supply: float) -> float:
    log_low, log_high = math.log(low), math.log(high)
    for _ in range(BISECTION_STEPS):
        if log_high - log_low < BISECTION_RELATIVE_WIDTH:
            break
        middle = 0.5 * (log_low + log_high)
        if demand(math.exp(middle)) > supply:
            log_low = middle
        else:
            log_high = middle
    return math.exp(log_high)


def _price_scale(bids: Sequence[Bid], last_price: Optional[float]) -> float:
    references = [bid.reference_price for bid in bids if bid.reference_price > 0.0]
    if references:
        return math.fsum(references) / len(references)
    return last_price if last_price and last_price > 0.0 else 1.0


def clear(bids: Sequence[Bid], offers: Sequence[Offer], good: GoodId, area: AreaId,
          currency: CurrencyId, last_price: Optional[float]) -> ClearingResult:
    """Clear one market for one year. Deterministic whatever the order of `bids` and `offers`."""
    bids = sorted(bids, key=lambda bid: (bid.priority, bid.buyer, bid.tile))
    offers = sorted((offer for offer in offers if offer.quantity > 0.0),
                    key=lambda offer: (offer.reservation_price, offer.seller, offer.tile))
    held_price = last_price if last_price is not None else 0.0
    if not offers:
        return _empty(good, area, currency, held_price, bids)

    minimum_price = MINIMUM_PRICE_SHARE_OF_REFERENCE * _price_scale(bids, last_price)
    effective = [max(offer.reservation_price, minimum_price) for offer in offers]
    demand = _demand_function(bids)

    if demand(effective[0]) <= 0.0:
        lowest = offers[0].reservation_price
        price = held_price if last_price is not None and lowest <= last_price else lowest
        supply = math.fsum(offer.quantity for offer, reservation in zip(offers, effective)
                           if reservation <= max(price, minimum_price))
        return _empty(good, area, currency, price, bids, supply)

    levels, running = [], 0.0
    for reservation, group in groupby(zip(effective, offers), key=lambda pair: pair[0]):
        running += math.fsum(offer.quantity for _, offer in group)
        levels.append((reservation, running))
    price = _solve_price(levels, demand)

    eligible = [(reservation, offer) for reservation, offer in zip(effective, offers)
                if reservation <= price]
    supply = math.fsum(offer.quantity for _, offer in eligible)
    wanted = demand(price)
    buyer_fills = _ration_buyers(bids, price, min(wanted, supply))
    traded = math.fsum(quantity for _, quantity in buyer_fills)
    seller_fills = _fill_sellers(eligible, traded)

    fills = tuple(Fill(bid.buyer, good, area, bid.tile, quantity, price, "buy")
                  for bid, quantity in buyer_fills if quantity > 0.0)
    fills += tuple(Fill(offer.seller, good, area, offer.tile, quantity, price, "sell")
                   for offer, quantity in seller_fills if quantity > 0.0)
    got: Dict[int, float] = {id(bid): quantity for bid, quantity in buyer_fills}
    unmet = math.fsum(max(0.0, bid.floor_quantity - got.get(id(bid), 0.0)) for bid in bids)
    return ClearingResult(good, area, currency, price, traded, wanted, supply, unmet, fills)


def _ration_buyers(bids: Sequence[Bid], price: float, available: float) -> List[Tuple[Bid, float]]:
    """Serve each tier in turn; a tier that cannot be served in full shares what is left pro rata."""
    result: List[Tuple[Bid, float]] = []
    remaining = available
    for _tier, tier_group in groupby(bids, key=lambda bid: bid.priority):
        tier_bids = list(tier_group)
        wants = [quantity_at(bid, price) for bid in tier_bids]
        total = math.fsum(wants)
        if total <= 0.0:
            result.extend((bid, 0.0) for bid in tier_bids)
        elif remaining >= total:
            result.extend(zip(tier_bids, wants))
            remaining -= total
        else:
            share = remaining / total
            result.extend((bid, want * share) for bid, want in zip(tier_bids, wants))
            remaining = 0.0
    return result


def _fill_sellers(eligible: List[Tuple[float, Offer]], traded: float) -> List[Tuple[Offer, float]]:
    """Cheapest reservations sell fully; the group at the marginal reservation shares what is left pro rata."""
    result: List[Tuple[Offer, float]] = []
    remaining = traded
    for _reservation, group in groupby(eligible, key=lambda pair: pair[0]):
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
