"""A seller left with unsold stock lowers its ask within the year's clearing until the stock sells or the ask
reaches the seller's floor, what a unit is worth to it unsold: the cheaper of making it again and holding it
for a year, but never below what the last unit fetches kept for the buyers it expects in later years.

Only producers whose ask is the one `producers.offers` gave them are searched: a seller that moves the price
chose its ask against the whole book (seller_offers.py) and holds units back on purpose. When any of them
is unsold, all of them are brought down to a common ask level, each to no lower than its own floor, because
a seller that undercuts leaves its rivals unsold in turn; the level is the highest at which all of them sell
out or sit at their floors, found by bisection on whole-market clears. A market with no unsold searchable
stock clears once, and a sold-out seller's ask is raised between years by ask_raise.py.
"""
import math
from typing import List, Optional, Sequence, Tuple

from sim.book import ROUNDING_SHARE

from . import goods_market, inventory, seller_offers
from .types import Offer

SEARCH_PRECISION = 1e-4     # numerical tolerance of the bisection on the ask level, not a model number


def _sold_by_offer(result, offers: Sequence[Offer]) -> dict:
    sold = {}
    for fill in result.fills:
        if fill.side == "sell":
            key = (fill.agent, fill.tile)
            sold[key] = sold.get(key, 0.0) + fill.quantity
    return sold


def _unsold(sold: dict, offers: Sequence[Offer], indices: Sequence[int]) -> List[int]:
    return [index for index in indices
            if sold.get((offers[index].seller, offers[index].tile), 0.0) < offers[index].quantity * (1.0 - ROUNDING_SHARE)]


def _floors(setup, record, view, offers: Sequence[Offer], original: Sequence[Offer], costs: dict) -> dict:
    """Searchable offers (index -> floor): a producer's unchanged ask above what a unit is worth to it unsold.
    `costs` holds the unit costs the market's sellers already worked out ((seller, tile) -> cost or None)."""
    floors = {}
    for index, offer in enumerate(offers):
        if offer.quantity <= 0.0 or offer.reservation_price != original[index].reservation_price:
            continue
        key = (offer.seller, offer.tile)
        cost = costs[key] if key in costs else seller_offers.unit_cost(setup, record, view, offer)
        if cost is None:
            continue
        floor = max(seller_offers.unit_value(offer, cost), _held_value(setup, record, view, offer))
        if offer.reservation_price > floor:
            floors[index] = floor
    return floors


def _held_value(setup, record, view, offer: Offer) -> float:
    """What the offer's last unit is worth to its producer kept for later sales (inventory.queued_holding_value):
    a seller that expects buyers next year does not sell a storable good below that this year."""
    producer = record.producers[offer.seller]
    recipe = setup.recipes[producer.recipe_id]
    spec = setup.specs.get(offer.good)
    rate = view.interest_rate(view.currency_of(offer.area))
    return inventory.queued_holding_value(offer.reservation_price, offer.quantity,
                                          producer.expected_sales * recipe.outputs.get(offer.good, 0.0), rate,
                                          spec.spoilage_per_year if spec is not None else 0.0)


def _with_level(offers: Sequence[Offer], floors: dict, level: float) -> List[Offer]:
    return [Offer(each.seller, each.good, each.area, each.tile, each.quantity,
                  min(each.reservation_price, max(floors[index], level))) if index in floors else each
            for index, each in enumerate(offers)]


def clear_with_search(setup, record, view, bids, original: Sequence[Offer], offers: Sequence[Offer], good, area,
                      currency, last_price: Optional[float], costs: Optional[dict] = None) -> Tuple[List[Offer], object]:
    """(the offers after the search, the market's clearing with them). `original` are the offers before the
    sellers re-chose, `offers` after; a market with no unsold searchable stock clears once."""
    offers = list(offers)
    buyers = goods_market.Buyers(bids, last_price)       # the same bids meet every trial book
    result = goods_market.clear(bids, offers, good, area, currency, last_price, buyers)
    floors = _floors(setup, record, view, offers, original, costs if costs is not None else {})
    unsold = _unsold(_sold_by_offer(result, offers), offers, list(floors))
    if not unsold:
        return offers, result
    searched = list(floors)       # a seller undercut by a lower ask becomes unsold in turn: all are searched together

    def trial(level: float):
        candidate = _with_level(offers, {index: floors[index] for index in searched}, level)
        sold = goods_market.sold_by_seller(buyers, candidate)       # the fills are built once, for the level kept
        return candidate, [index for index in _unsold(sold, candidate, searched)
                           if candidate[index].reservation_price > floors[index]]

    low = min(floors[index] for index in searched)
    best = trial(low)         # every searched ask at its floor: nothing above a floor can stay unsold
    high = max(offers[index].reservation_price for index in searched)
    ceiling = high
    # the gap is judged against the level itself, or against the highest ask when the floor is zero: a bracket
    # [0, high] never closes relative to its own shrinking top
    while high - low > SEARCH_PRECISION * (high if low > 0.0 else ceiling):
        # geometric mean as the product of roots: the product of a tiny floor and an ask underflows
        middle = math.sqrt(low) * math.sqrt(high) if low > 0.0 else 0.5 * (low + high)
        attempt = trial(middle)
        if attempt[1]:
            high = middle
        else:
            low, best = middle, attempt
    return best[0], goods_market.clear(bids, best[0], good, area, currency, last_price, buyers)
