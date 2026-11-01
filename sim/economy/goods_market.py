"""One market's clearing within a year: buyers' schedules against sellers' asks.

Each buyer splits its demand over the sellers by the logit on their asks, every seller sells at its own ask, and what a
sold-out seller could not serve is sent again to the sellers still holding stock (goods_market_logit.py, after
Eurace@Unibi's households and malls). A seller's ask is the `reservation_price` of its offer. The market has no single
price: `ClearingResult.price` is the quantity-weighted mean of what traded, for the callers that need one figure (the
price index, merchants, the market's memory). Buyers are served by priority tier (lower first) when a seller runs short.

`clear_at_one_price` is the other rule, a uniform-price call market (supply a step function at reservations, demand the
sum of the buyers' schedules, lowest reservations sell first): it answers "at what price would these buyers take
exactly this supply", which the callers probing hypothetical supply (market_curves.py, expansion_price.py) ask.

Choices:
  * Prices are positive. An ask at or below zero (a waste product) is treated as the lowest price the market
    considers, so such a seller sells at that token price and the price never clears below zero.
  * With no offers there is no trade, every floor unmet. With no demand nothing sells. A result with no
    trade has no price (`traded_price` is None) and a `quote` instead (market_quote.py); its `price`
    field is a held or lowest-ask figure the caller may read, not a price anyone traded at.
"""
import bisect
import math
from functools import cached_property
from itertools import groupby
from operator import attrgetter, itemgetter
from typing import List, Optional, Sequence, Tuple

from sim.constants import declare

from .accounts import ROUNDING_SHARE
from .goods_market_demand import DemandSchedule
from .goods_market_fills import buyer_fills, make_fill, seller_fills, without_edge_self_trades
from .goods_market_logit import allocate
from .goods_market_ration import ration
from .goods_market_solve import solve_price
from . import market_quote
from .types import AreaId, Bid, ClearingResult, CurrencyId, Fill, GoodId, Offer

MINIMUM_PRICE_SHARE_OF_REFERENCE = declare(
    "MINIMUM_PRICE_SHARE_OF_REFERENCE", 1e-3, kind="temporary_heuristic",
    unit="share of the buyers' mean reference price",
    source=None, confidence="D",
    why="Prices clear on positive values, so a seller ready to pay to be rid of a good (reservation "
        "at or below zero) is placed at a token price instead. The token is a small share of the "
        "price scale buyers quote; waste disposal charged to the seller is not yet modelled.")
_BID_ORDER = attrgetter("priority", "buyer", "tile")
_OFFER_ORDER = attrgetter("reservation_price", "seller", "tile")
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


def _empty(good, area, currency, price, bids, supply_at_price=0.0, offers=()) -> ClearingResult:
    unmet = math.fsum(max(0.0, bid.floor_quantity) for bid in bids)
    return ClearingResult(good, area, currency, price, 0.0, 0.0, supply_at_price, unmet, (),
                          market_quote.no_trade_quote(bids, offers))


def _price_scale(bids: Sequence[Bid], last_price: Optional[float]) -> float:
    references = [bid.reference_price for bid in bids if bid.reference_price > 0.0]
    if references:
        return math.fsum(references) / len(references)
    return last_price if last_price and last_price > 0.0 else 1.0


class Buyers:
    """One market's bids in clearing order with their demand schedule, built once for any number of clears."""

    def __init__(self, bids: Sequence[Bid], last_price: Optional[float]):
        self.bids = sorted(bids, key=_BID_ORDER)
        self.minimum_price = MINIMUM_PRICE_SHARE_OF_REFERENCE * _price_scale(self.bids, last_price)
        self.last_price = last_price
        self._wants: dict = {}     # price -> (each buyer's want, their total)
        self._traded: dict = {}    # (price, quantity available) -> what the buyers are served in all

    @cached_property
    def schedule(self) -> DemandSchedule:
        """The bids' demand schedule, built when a market with offers first reads it."""
        return DemandSchedule(self.bids)

    def traded_at(self, price: float, supply: float) -> float:
        """The total the buyers are served at a price when `supply` is on offer there."""
        wants = self._wants.get(price)
        if wants is None:
            each = self.schedule.each_at(price)
            wants = self._wants[price] = (each, math.fsum(each))
        available = min(wants[1], supply)
        key = (price, available)
        traded = self._traded.get(key)
        if traded is None:
            traded = self._traded[key] = math.fsum(ration(self.bids, wants[0], available))
        return traded


def in_clearing_order(offers: Sequence[Offer]) -> List[Offer]:
    """The offers a market clears, cheapest reservation first."""
    return sorted((offer for offer in offers if offer.quantity > 0.0), key=_OFFER_ORDER)


def with_offer(ordered: List[Offer], offer: Offer) -> List[Offer]:
    """`ordered` (in clearing order) with one more offer put in its place, as `in_clearing_order` would."""
    if offer.quantity <= 0.0:
        return ordered
    result = list(ordered)
    bisect.insort(result, offer, key=_OFFER_ORDER)
    return result


def clear_at_one_price(bids: Sequence[Bid], offers: Sequence[Offer], good: GoodId, area: AreaId,
                       currency: CurrencyId, last_price: Optional[float], buyers: Optional[Buyers] = None) -> ClearingResult:
    """Clear one market for one year at one price: where the buyers' schedules meet the sellers' reservations, the
    lowest reservations selling first and the marginal group pro rata. Deterministic whatever the order of `bids` and
    `offers`. `buyers` is `Buyers(bids, last_price)` when the caller clears the same bids against several books."""
    if buyers is None:
        buyers = Buyers(bids, last_price)
    bids = buyers.bids
    price, eligible, supply, wants = _crossing(buyers, in_clearing_order(offers))
    if eligible is None:
        return _empty(good, area, currency, price, bids, supply, offers)
    wanted = math.fsum(wants)
    served = ration(bids, wants, min(wanted, supply))
    traded = math.fsum(served)
    seller_quantities = _fill_sellers(eligible, traded)

    fills = buyer_fills(bids, served, good, area, price)
    fills.extend(seller_fills(seller_quantities, good, area, price))
    fills, wash = without_edge_self_trades(fills)
    traded -= wash
    unmet = math.fsum([max(0.0, bid.floor_quantity - quantity) for bid, quantity in zip(bids, served)])
    return ClearingResult(good, area, currency, price, traded, wanted, supply, unmet, tuple(fills))


def clear(bids: Sequence[Bid], offers: Sequence[Offer], good: GoodId, area: AreaId,
          currency: CurrencyId, last_price: Optional[float], buyers: Optional[Buyers] = None) -> ClearingResult:
    """Clear one market for one year: buyers choose among the sellers by the logit on their asks, each seller sells at
    its own ask, the result's price is the mean of what traded. Deterministic whatever the order of `bids` and `offers`.
    `buyers` is `Buyers(bids, last_price)` when the caller clears the same bids against several books."""
    if buyers is None:
        buyers = Buyers(bids, last_price)
    bids = buyers.bids
    ordered = in_clearing_order(offers)
    asks = _asks(buyers, ordered)
    supply = math.fsum(offer.quantity for offer in ordered)
    if not _trades(buyers, ordered, asks):
        return _empty(good, area, currency, _held_price(buyers, asks), bids, supply, offers)
    allocation = allocate(bids, ordered, asks, buyers.schedule)
    fills: List[Fill] = []
    unmet = 0.0
    for bid, quantity, cost in zip(bids, allocation.quantity, allocation.cost):
        unmet += max(0.0, bid.floor_quantity - quantity)
        if quantity > 0.0:
            fills.extend(buyer_fills([bid], [quantity], good, area, cost / quantity))
    fills.extend(make_fill(offer.seller, good, area, offer.tile, amount, ask, "sell")
                 for offer, amount, ask in zip(ordered, allocation.sold, asks) if amount > 0.0)
    fills, wash = without_edge_self_trades(fills)
    sales = [fill for fill in fills if fill.side == "sell"]
    traded = math.fsum(fill.quantity for fill in sales)
    if not traded > 0.0:
        return _empty(good, area, currency, _held_price(buyers, asks), bids, supply, offers)
    mean = math.fsum(fill.quantity * fill.price for fill in sales) / traded
    return ClearingResult(good, area, currency, mean, traded, allocation.requested, supply, unmet, tuple(fills))


def _asks(buyers: Buyers, ordered: Sequence[Offer]) -> List[float]:
    """The prices the offers are sold at: each ask, none below the token price that keeps prices positive."""
    return [max(offer.reservation_price, buyers.minimum_price) for offer in ordered]


def _trades(buyers: Buyers, ordered: Sequence[Offer], asks: Sequence[float]) -> bool:
    """False when nothing can sell: no offers, only float residue on offer (clearing it would print a price set by nothing
    a seller meant to sell), or no buyer wants anything even at the lowest ask (the buyers want less the dearer the ask)."""
    if not ordered:
        return False
    wanted = buyers.schedule.total_at(asks[0])
    return wanted > 0.0 and math.fsum(offer.quantity for offer in ordered) > ROUNDING_SHARE * wanted


def _held_price(buyers: Buyers, asks: Sequence[float]) -> float:
    """The figure a market that did not trade carries as its price: the last price held, or the lowest ask when that is
    above it (and zero with neither; the result has a quote, not a price)."""
    last_price = buyers.last_price
    held = last_price if last_price is not None else 0.0
    if not asks or (last_price is not None and asks[0] <= last_price):
        return held
    return asks[0]


def sold_by_seller(buyers: Buyers, offers: Sequence[Offer]) -> dict:
    """(seller, tile) -> what that seller's offers sell there, as the sell fills of `clear` add up (a non-edge
    seller's fills are untouched by self-trade washing), without building fills."""
    ordered = in_clearing_order(offers)
    asks = _asks(buyers, ordered)
    sold: dict = {}
    if not _trades(buyers, ordered, asks):
        return sold
    allocation = allocate(buyers.bids, ordered, asks, buyers.schedule)
    for offer, quantity in zip(ordered, allocation.sold):
        if quantity > 0.0:
            key = (offer.seller, offer.tile)
            sold[key] = sold.get(key, 0.0) + quantity
    return sold


def requested_by_buyers(buyers: Buyers, offers: Sequence[Offer]) -> float:
    """What the buyers ask for at the offers' asks before any seller runs out (`ClearingResult.demand_at_price` of the same
    book), without building fills; nothing when the book does not trade."""
    ordered = in_clearing_order(offers)
    asks = _asks(buyers, ordered)
    if not _trades(buyers, ordered, asks):
        return 0.0
    return allocate(buyers.bids, ordered, asks, buyers.schedule).requested


def price_and_sold(buyers: Buyers, ordered: List[Offer], seller: str) -> Tuple[float, float]:
    """The clearing price and what a seller that is not a book edge sells, as `clear` gives them, without
    building fills. `ordered` is in clearing order (`in_clearing_order`, `with_offer`)."""
    price, eligible, supply, _wants = _crossing(buyers, ordered, with_wants=False)
    if eligible is None:
        return price, 0.0
    # `_fill_sellers` for this seller's offers alone
    remaining, sold = buyers.traded_at(price, supply), []
    for _reservation, group in groupby(eligible, key=_FIRST):
        offers = [offer for _, offer in group]
        total = math.fsum(offer.quantity for offer in offers)
        own = [offer.quantity for offer in offers if offer.seller == seller]
        if remaining >= total:
            sold.extend(own)
            remaining -= total
        else:
            share = remaining / total if total > 0.0 else 0.0
            sold.extend(quantity * share for quantity in own)
            remaining = 0.0
    return price, math.fsum(quantity for quantity in sold if quantity > 0.0)


def _crossing(buyers: Buyers, offers: List[Offer], with_wants: bool = True):
    """(price, offers eligible at it, supply, each buyer's want at it) where `offers` (in clearing order) meet
    the buyers; the eligible offers and wants are None when nothing trades, and supply is then what would
    sell at the price. Without `with_wants` the wants are left out (None)."""
    last_price = buyers.last_price
    held_price = last_price if last_price is not None else 0.0
    if not offers:
        return held_price, None, 0.0, None

    minimum_price = buyers.minimum_price
    effective = [max(offer.reservation_price, minimum_price) for offer in offers]
    schedule = buyers.schedule

    demand_at_first = schedule.total_at(effective[0])
    if math.fsum(offer.quantity for offer in offers) <= ROUNDING_SHARE * demand_at_first:
        # what is on offer is float residue left in a stock, not supply: clearing it would print a price
        # set by nothing a seller meant to sell
        return held_price, None, 0.0, None
    if demand_at_first <= 0.0:
        lowest = effective[0]
        price = held_price if last_price is not None and lowest <= last_price else lowest
        supply = math.fsum(offer.quantity for offer, reservation in zip(offers, effective)
                           if reservation <= max(price, minimum_price))
        return price, None, supply, None

    levels, running = [], 0.0
    for reservation, group in groupby(zip(effective, offers), key=_FIRST):
        running += math.fsum(offer.quantity for _, offer in group)
        levels.append((reservation, running))
    price = solve_price(levels, schedule.total_at, demand_at_first,
                        schedule.uncapped_at if schedule.distinct_schedules() * CHEAP_PASSES_PER_BID <= len(buyers.bids)
                        else None, schedule.solutions)
    if schedule.price_capped:
        price = at_a_ceiling(price, schedule, levels, effective[0])

    eligible = [(reservation, offer) for reservation, offer in zip(effective, offers)
                if reservation <= price]
    supply = math.fsum(offer.quantity for _, offer in eligible)
    return price, eligible, supply, schedule.each_at(price) if with_wants else None


def at_a_ceiling(price: float, schedule, levels, lowest: float) -> float:
    """Where demand falls off a buyer's ceiling, the crossing can sit just above it with nothing
    wanted: then the market clears at that ceiling, with buyers rationed to the supply there. A ceiling
    only clears the market if what is still wanted just above it fits in the supply at it; otherwise the
    buyers left would bid on past it to the next seller's step, where the crossing already is."""
    if schedule.total_at(price) >= _supply_at(levels, price):
        return price
    for ceiling in schedule.ceilings_descending():
        if not lowest <= ceiling <= price:
            if ceiling < lowest:
                break
            continue
        supply = _supply_at(levels, ceiling)
        if (schedule.total_at(ceiling) >= supply
                and schedule.total_at(ceiling * (1.0 + ROUNDING_SHARE)) <= supply * (1.0 + ROUNDING_SHARE)):
            return ceiling
    return price


def _supply_at(levels, price: float) -> float:
    """Cumulative supply of the last level at or below `price` (levels ascend by reservation)."""
    count = bisect.bisect_right(levels, price, key=_FIRST)
    return levels[count - 1][1] if count else 0.0


def _ration_buyers(bids: Sequence[Bid], price: float, available: float) -> List[Tuple[Bid, float]]:
    """Each buyer's served quantity at a price with `available` to share, in the order of `bids`."""
    served = ration(bids, [quantity_at(bid, price) for bid in bids], available)
    return list(zip(bids, served))


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
