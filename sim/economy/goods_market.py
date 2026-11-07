"""One market's clearing within a year: buyers' schedules against sellers' asks.

Each buyer splits its demand over the sellers by the logit on their asks, every seller sells at its own ask, and what a
sold-out seller could not serve is sent again to the sellers still holding stock (goods_market_logit.py, after
Eurace@Unibi's households and malls). A seller's ask is the `reservation_price` of its offer. The market has no single
price: `ClearingResult.price` is the quantity-weighted mean of what traded, for the callers that need one figure (the
price index, merchants, the market's memory). Buyers are served by priority tier (lower first) when a seller runs short.

`clear_at_one_price` is the other rule, a uniform-price call market (supply a step function at reservations, demand the
sum of the buyers' schedules, lowest reservations sell first): it answers "at what price would these buyers take
exactly this supply", which the callers probing hypothetical supply (market_curves.py) ask; expansion_price.py reads its crossing
(`crossing`).

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
from typing import Dict, List, Optional, Sequence, Tuple

import numpy

from sim.constants import declare

from sim.book import EDGE_PREFIX, ROUNDING_SHARE
from . import goods_market_kernels
from .goods_market_demand import DemandArrays, DemandSchedule
from .goods_market_fills import buyer_fills, make_fill, seller_fills, without_edge_self_trades, without_washed
from .goods_market_logit import allocate
from .goods_market_ration import ration
from .goods_market_solve import solve_price
from . import market_quote
from .types import AreaId, Bid, ClearingResult, CurrencyId, Fill, GoodId, Offer, Pairing, is_edge

MINIMUM_PRICE_SHARE_OF_REFERENCE = declare(
    "MINIMUM_PRICE_SHARE_OF_REFERENCE", 1e-3, kind="temporary_heuristic",
    unit="share of the buyers' mean reference price",
    source=None, confidence="D",
    why="Prices clear on positive values, so a seller ready to pay to be rid of a good (reservation "
        "at or below zero) is placed at a token price instead. The token is a small share of the "
        "price scale buyers quote; waste disposal charged to the seller is not yet modelled.")
_BID_ORDER = attrgetter("priority", "buyer", "tile")
_OFFER_ORDER = attrgetter("reservation_price", "seller", "tile")
_SELLER_KEY = attrgetter("seller", "tile")
_BUYER_KEY = attrgetter("buyer", "tile")
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


def _empty(good, area, currency, price: Optional[float], bids, supply_at_price=0.0, offers=()) -> ClearingResult:
    return ClearingResult(good, area, currency, price, 0.0, 0.0, supply_at_price, (),
                          market_quote.no_trade_quote(bids, offers))


def _price_scale(bids: Sequence[Bid], last_price: Optional[float]) -> Optional[float]:
    """The mean reference price the buyers quote, else the last price; None when neither exists."""
    references = [bid.reference_price for bid in bids if bid.reference_price > 0.0]
    if references:
        return math.fsum(references) / len(references)
    return last_price if last_price and last_price > 0.0 else None


class Buyers:
    """One market's bids in clearing order with their demand schedule, built once for any number of clears."""

    def __init__(self, bids: Sequence[Bid], last_price: Optional[float]):
        self.bids = sorted(bids, key=_BID_ORDER)
        scale = _price_scale(self.bids, last_price)
        self.minimum_price = None if scale is None else MINIMUM_PRICE_SHARE_OF_REFERENCE * scale   # None: no unit to tie a token price to
        self.last_price = last_price

    def at_least_minimum(self, price: float) -> float:
        """`price`, raised to the minimum price when there is one."""
        return price if self.minimum_price is None else max(price, self.minimum_price)

    @cached_property
    def arrays(self) -> DemandArrays:
        """The bids packed for the clearing kernels, built when a market with offers first reads it."""
        return DemandArrays(self.bids)

    @cached_property
    def schedule(self) -> DemandSchedule:
        """The bids' demand schedule, built when a market with offers first reads it."""
        return DemandSchedule(self.bids)


def in_clearing_order(offers: Sequence[Offer]) -> List[Offer]:
    """The offers a market clears, cheapest reservation first."""
    return sorted((offer for offer in offers if offer.quantity > 0.0), key=_OFFER_ORDER)


def clear_at_one_price(bids: Sequence[Bid], offers: Sequence[Offer], good: GoodId, area: AreaId,
                       currency: CurrencyId, last_price: Optional[float], buyers: Optional[Buyers] = None) -> ClearingResult:
    """Clear one market for one year at one price: where the buyers' schedules meet the sellers' reservations, the
    lowest reservations selling first and the marginal group pro rata. Deterministic whatever the order of `bids` and
    `offers`. `buyers` is `Buyers(bids, last_price)` when the caller clears the same bids against several books."""
    if buyers is None:
        buyers = Buyers(bids, last_price)
    bids = buyers.bids
    price, eligible, supply, wants = crossing(buyers, in_clearing_order(offers))
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
    wanted -= wash      # the washed quantity was neither wanted by a real buyer nor left unmet
    return ClearingResult(good, area, currency, price, traded, wanted, supply, tuple(fills))


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
    allocation = allocate(bids, ordered, asks, buyers.arrays)
    fills: List[Fill] = [make_fill(bid.buyer, good, area, bid.tile, quantity, cost / quantity, "buy")
                         for bid, quantity, cost in zip(bids, allocation.quantity, allocation.cost) if quantity > 0.0]
    fills.extend(make_fill(offer.seller, good, area, offer.tile, amount, ask, "sell")
                 for offer, amount, ask in zip(ordered, allocation.sold, asks) if amount > 0.0)
    pairing, washed = _pairing(bids, ordered, asks, allocation.flow)
    fills = without_washed(fills, washed)
    wash = math.fsum(washed.values())
    sales = [fill for fill in fills if fill.side == "sell"]
    traded = math.fsum(fill.quantity for fill in sales)
    if not traded > 0.0:
        return _empty(good, area, currency, _held_price(buyers, asks), bids, supply, offers)
    mean = math.fsum(fill.quantity * fill.price for fill in sales) / traded
    return ClearingResult(good, area, currency, mean, traded, allocation.requested - wash, supply, tuple(fills),
                          pairing=pairing)


def _pairing(bids: Sequence[Bid], ordered: Sequence[Offer], asks: Sequence[float], flow) -> Tuple[Pairing, Dict[str, float]]:
    """Who bought from whom, from the allocation's offer-by-bid quantities; a book edge's purchase of its own offer is no
    trade and is left out of the pairing and returned as the quantity washed per edge."""
    sellers = tuple(map(_SELLER_KEY, ordered))
    buyers = tuple(map(_BUYER_KEY, bids))
    seller_index, buyer_index = numpy.nonzero(flow > 0.0)
    quantity = flow[seller_index, buyer_index].tolist()
    seller_index, buyer_index = seller_index.tolist(), buyer_index.tolist()
    washed: Dict[str, float] = {}
    if not any(seller.startswith(EDGE_PREFIX) for seller, _tile in sellers):
        return Pairing(buyers, sellers, tuple(asks), tuple(buyer_index), tuple(seller_index), tuple(quantity)), washed
    kept = []
    for pair in range(len(quantity)):
        seller = sellers[seller_index[pair]][0]
        if is_edge(seller) and seller == buyers[buyer_index[pair]][0]:
            washed[seller] = washed.get(seller, 0.0) + quantity[pair]
        else:
            kept.append(pair)
    return (Pairing(buyers, sellers, tuple(asks), tuple(buyer_index[pair] for pair in kept),
                    tuple(seller_index[pair] for pair in kept), tuple(quantity[pair] for pair in kept)), washed)


def _asks(buyers: Buyers, ordered: Sequence[Offer]) -> List[float]:
    """The prices the offers are sold at: each ask, none below the token price that keeps prices positive."""
    return [buyers.at_least_minimum(offer.reservation_price) for offer in ordered]


def _trades(buyers: Buyers, ordered: Sequence[Offer], asks: Sequence[float]) -> bool:
    """False when nothing can sell: no offers, only float residue on offer (clearing it would print a price set by nothing
    a seller meant to sell), or no buyer wants anything even at the lowest ask (the buyers want less the dearer the ask)."""
    if not ordered:
        return False
    wanted = goods_market_kernels.total_wanted(asks[0], *buyers.arrays.kernel_arrays())
    return wanted > 0.0 and math.fsum(offer.quantity for offer in ordered) > ROUNDING_SHARE * wanted


def _held_price(buyers: Buyers, asks: Sequence[float]) -> Optional[float]:
    """The figure a market that did not trade carries as its price: the last price held, or the lowest ask when that is
    above it (None with neither; the result has a quote, not a price)."""
    last_price = buyers.last_price
    if not asks or (last_price is not None and asks[0] <= last_price):
        return last_price
    return asks[0]


def sold_by_seller(buyers: Buyers, offers: Sequence[Offer]) -> dict:
    """(seller, tile) -> what that seller's offers sell there, as the sell fills of `clear` add up (a non-edge
    seller's fills are untouched by self-trade washing), without building fills."""
    ordered = in_clearing_order(offers)
    asks = _asks(buyers, ordered)
    sold: dict = {}
    if not _trades(buyers, ordered, asks):
        return sold
    allocation = allocate(buyers.bids, ordered, asks, buyers.arrays)
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
    quantities = numpy.fromiter((offer.quantity for offer in ordered), dtype=float, count=len(ordered))
    return float(goods_market_kernels.requested_round_one(numpy.array(asks, dtype=float), quantities,
                                                          *buyers.arrays.kernel_arrays()))


def crossing(buyers: Buyers, offers: List[Offer], with_wants: bool = True):
    """(price, offers eligible at it, supply, each buyer's want at it) where `offers` (in clearing order) meet
    the buyers; the eligible offers and wants are None when nothing trades, and supply is then what would
    sell at the price. Without `with_wants` the wants are left out (None)."""
    last_price = buyers.last_price
    held_price = last_price     # None with no last price: nothing was held
    if not offers:
        return held_price, None, 0.0, None

    effective = [buyers.at_least_minimum(offer.reservation_price) for offer in offers]
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
                           if reservation <= buyers.at_least_minimum(price))
        return price, None, supply, None

    levels, running = [], 0.0
    floor = _smallest_price(effective, last_price)    # the solver searches in log price: a level at zero would have no log
    if floor is None:      # demand with no price scale at all and sellers at zero: no price is set by it
        return held_price, None, 0.0, None
    for reservation, group in groupby(zip(effective, offers), key=_FIRST):
        running += math.fsum(offer.quantity for _, offer in group)
        levels.append((max(reservation, floor), running))
    price = solve_price(levels, schedule.total_at, demand_at_first,
                        schedule.uncapped_at if schedule.distinct_schedules() * CHEAP_PASSES_PER_BID <= len(buyers.bids)
                        else None, schedule.solutions)
    if schedule.price_capped:
        price = at_a_ceiling(price, schedule, levels, effective[0])

    eligible = [(reservation, offer) for reservation, offer in zip(effective, offers)
                if reservation <= price]
    supply = math.fsum(offer.quantity for _, offer in eligible)
    return price, eligible, supply, schedule.each_at(price) if with_wants else None


def _smallest_price(reservations: Sequence[float], last_price: Optional[float]) -> Optional[float]:
    """The price a level at zero is searched from: the lowest positive reservation, else the last price; None when
    the book has neither. Only the search uses it; a zero reservation still sells at any price."""
    positive = [reservation for reservation in reservations if reservation > 0.0]
    if positive:
        return min(positive)
    return last_price if last_price is not None and last_price > 0.0 else None


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
