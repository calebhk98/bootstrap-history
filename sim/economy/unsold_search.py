"""A seller left with unsold stock lowers its ask within the year's clearing until the stock sells or the ask
reaches the seller's floor, what a unit is worth to it unsold: the cheaper of making it again and holding it
for a year, but never below what the last unit fetches kept for the buyers it expects in later years.

Only producers whose ask is the one `producers.offers` gave them are searched: a seller that re-priced
(price_setting.py, via seller_offers.py) chose its ask against the other sellers' on purpose. When any of them
is unsold, all of them are brought down to a common ask level, each to no lower than its own floor, because
a seller that undercuts leaves its rivals unsold in turn; the level is the highest at which all of them sell
out or sit at their floors, found by bisection on whole-market clears. A market with no unsold searchable
stock clears once, and a seller's ask is moved between years by its stock against the target (ask_adjust.py).
The mirror runs after it: producers whose buyers were turned away raise their asks to where the buyers still ask for
the whole stock (demand_search.py).
"""
import math
from typing import List, Optional, Sequence, Tuple

from sim.book import ROUNDING_SHARE

from . import demand_search, goods_market, inventory, seller_offers, titles_value
from .ask_adjust import band_edge
from .types import Offer

UNSOLD_BOUND_MARGIN = 1e-12    # float noise of two sums of the same demand, not a model number
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
    """Searchable offers (index -> floor): a producer's unchanged ask above what a unit is worth to it unsold, or an ask
    opened from a reservation of nothing (seller_offers.opened_ask), whose unit is worth nothing unsold.
    `costs` holds the unit costs the market's sellers already worked out ((seller, tile) -> cost or None)."""
    floors = {}
    for index, offer in enumerate(offers):
        opened = original[index].reservation_price <= 0.0 < offer.reservation_price
        crowd = seller_offers.stands_for_many(record, offer)      # a crowd's ask is lifted to its expectation, not re-priced
        if offer.quantity <= 0.0 or (offer.reservation_price != original[index].reservation_price and not opened and not crowd):
            continue
        key = (offer.seller, offer.tile)
        cost = costs[key] if key in costs else seller_offers.unit_cost(setup, record, view, offer)
        if cost is None:
            continue
        floor = max(seller_offers.unit_value(original[index], cost), _held_value(setup, record, view, original[index]))
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
    if spec is not None and not spec.portable:
        # ground never queues behind the stock: every hectare yields its rent while held
        return titles_value.hectare_value(record.land_rent.get(offer.tile, 0.0),
                                          titles_value.capitalising_rate(rate, setup.opening_rate))
    return inventory.queued_holding_value(offer.reservation_price, offer.quantity,
                                          producer.expected_sales * recipe.outputs.get(offer.good, 0.0), rate,
                                          spec.spoilage_per_year if spec is not None else 0.0)


def flood_price(wanted, held: float, lowest: float, highest: float, points: int = 200) -> float:
    """The price in [lowest, highest] at which a seller holding `held` units that are worth nothing unsold earns most from
    the buyers (`wanted(price)` is the quantity they want there): price times the smaller of the stock and the want, the
    highest such price when several earn alike. Asking less than this sells no more and takes less."""
    if not 0.0 < lowest < highest:
        return highest
    ratio = (highest / lowest) ** (1.0 / (points - 1))
    prices = [lowest * ratio ** step for step in range(points - 1)] + [highest]
    earnings = [price * min(held, wanted(price)) for price in prices]
    best = max(earnings)
    return max(price for price, earned in zip(prices, earnings) if earned >= best * (1.0 - 1e-9))


def _salvage_floors(floors: dict, offers: Sequence[Offer], buyers: goods_market.Buyers) -> dict:
    """`floors` with each floor of nothing (a unit worth nothing unsold) raised to the flood price of the stock so held:
    a perishable that cannot all sell asks what earns most, not the market's token price. An offer whose ask is not
    above its new floor is left out of the search."""
    held = math.fsum(offers[index].quantity for index, floor in floors.items() if floor <= 0.0)
    if held <= 0.0:
        return floors
    highest = max(offers[index].reservation_price for index, floor in floors.items() if floor <= 0.0)
    level = flood_price(buyers.schedule.total_at, held, buyers.minimum_price, highest)
    raised = {index: (level if floor <= 0.0 else floor) for index, floor in floors.items()}
    return {index: floor for index, floor in raised.items() if offers[index].reservation_price > floor}


def _with_level(offers: Sequence[Offer], floors: dict, level: float) -> List[Offer]:
    return [Offer(each.seller, each.good, each.area, each.tile, each.quantity,
                  min(each.reservation_price, max(floors[index], level))) if index in floors else each
            for index, each in enumerate(offers)]


def unsold_above_the_floor(buyers: goods_market.Buyers, offers: Sequence[Offer], floors: dict) -> bool:
    """True when every searched offer sharing one floor leaves some offer unsold at every level above that floor,
    so the search ends at the floor: at any such level every searched ask is above the floor, hence at or above
    the effective floor price, where the buyers want at most what they want there; when that is under what the
    searched offers hold (each of a distinct seller and tile) they cannot all sell out."""
    if len(set(floors.values())) != 1:
        return False
    keys = {(offers[index].seller, offers[index].tile) for index in floors}
    if len(keys) != len(floors):
        return False
    wanted = buyers.schedule.total_at(max(next(iter(floors.values())), buyers.minimum_price))
    held = math.fsum(offers[index].quantity for index in floors)
    return wanted * (1.0 + UNSOLD_BOUND_MARGIN) < held * (1.0 - ROUNDING_SHARE)


def clear_with_search(setup, record, view, bids, original: Sequence[Offer], offers: Sequence[Offer], good, area,
                      currency, last_price: Optional[float], costs: Optional[dict] = None) -> Tuple[List[Offer], object]:
    """(the offers after the search, the market's clearing with them). `original` are the offers before the
    sellers re-chose, `offers` after; a market with no unsold searchable stock clears once."""
    offers = list(offers)
    buyers = goods_market.Buyers(bids, last_price)       # the same bids meet every trial book
    result = goods_market.clear(bids, offers, good, area, currency, last_price, buyers)
    floors = _floors(setup, record, view, offers, original, costs if costs is not None else {})
    if floors and _unsold(_sold_by_offer(result, offers), offers, list(floors)):
        floors = _salvage_floors(floors, offers, buyers)
        if floors:
            offers, result = search_asks(bids, offers, floors, buyers, good, area, currency, last_price)
    return raise_sold_out(record, buyers, bids, offers, result, good, area, currency, last_price,
                          (setup, view, costs if costs is not None else {}))


def ask_limits(setup, record, view, offers: Sequence[Offer], indices: Sequence[int], costs: dict) -> dict:
    """index -> the most that producer may ask: the top of the band above its unit cost (ask_adjust.band_edge), the same
    limit its re-pricing and its carried ask keep to. A seller whose cost cannot be priced has no limit."""
    limits = {}
    for index in indices:
        offer = offers[index]
        key = (offer.seller, offer.tile)
        cost = costs[key] if key in costs else seller_offers.unit_cost(setup, record, view, offer)
        if cost is not None and math.isfinite(cost):
            limits[index] = band_edge(cost, seller_offers.input_share_of_cost(setup, record, view, offer),
                                      seller_offers.ask_band_multiple(setup, offer))
    return limits


def raise_sold_out(record, buyers: goods_market.Buyers, bids, offers: Sequence[Offer], result, good, area, currency,
                   last_price: Optional[float], pricing=None) -> Tuple[List[Offer], object]:
    """(the offers with the producers' asks raised to where they just sell out (demand_search.py), each held to the band
    above its cost; the market's clearing with them); a market in which buyers were not turned away is returned as it
    cleared. `pricing` is (setup, view, unit costs by (seller, tile)); without it the asks have no band."""
    if result.quantity >= result.demand_at_price * (1.0 - ROUNDING_SHARE):
        return list(offers), result
    producers = [index for index, offer in enumerate(offers) if offer.quantity > 0.0 and offer.seller in record.producers]
    limits = ask_limits(pricing[0], record, pricing[1], offers, producers, pricing[2]) if pricing else None
    raised = demand_search.raise_asks(buyers, offers, producers, limits)
    if raised == list(offers):
        return list(offers), result
    return raised, goods_market.clear(bids, raised, good, area, currency, last_price, buyers)


def search_asks(bids, offers: Sequence[Offer], floors: dict, buyers: goods_market.Buyers, good, area, currency,
                last_price: Optional[float]) -> Tuple[List[Offer], object]:
    """(the offers with the searched asks (index -> floor) brought down to the highest common level at which
    they sell out or sit at their floors, the market's clearing with them); some searched offer is unsold."""
    searched = list(floors)       # a seller undercut by a lower ask becomes unsold in turn: all are searched together

    def trial(level: float):
        candidate = _with_level(offers, {index: floors[index] for index in searched}, level)
        sold = goods_market.sold_by_seller(buyers, candidate)       # the fills are built once, for the level kept
        return candidate, [index for index in _unsold(sold, candidate, searched)
                           if candidate[index].reservation_price > floors[index]]

    low = min(floors[index] for index in searched)
    if unsold_above_the_floor(buyers, offers, floors):    # the bisection would end at the floor: skip its trials
        kept = _with_level(offers, floors, low)
        return kept, goods_market.clear(bids, kept, good, area, currency, last_price, buyers)
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
