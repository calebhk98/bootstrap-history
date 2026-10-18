"""The producers' offers in one market, re-chosen against that market's book before it clears.

Each producer in turn (by agent id) reads the buyers' schedules and the other sellers' current offers and,
if its own offer moves the clearing price (seller_pricing.py), asks the reservation that maximises its
profit; a producer that does not move the price keeps the reservation `producers.offers` gave it. What a
unit is worth to the seller unsold is the cheaper of replacing it (its variable cost per unit) and holding
it (its price-taking reservation), so a seller never prices below what a unit costs it to make or keep.
A producer that stands for several workshops (Producer.workshops above one) is not a seller but a crowd of
price takers: it keeps the price-taking reservation and neither searches nor raises, and offers it as a
rising schedule over its workshops' costs (crowd_offers.py). A seller that moves the price may also raise its ask above the price-taking one, which holds units back
(restraint) when the dearer, smaller sale earns more. A change either way is bounded by the share a seller
already marks its ask down in a year (UNSOLD_ASK_MARKDOWN_SHARE), so an ask moves over the years as the
book changes and never jumps in one; an ask raised past what buyers pay goes unsold and is marked down
again by the producer's own rule.

A seller's ask is also held to what a unit costs it times the markup a seller can charge when buyers can
substitute toward other goods meeting the same need (substitution_markup). Against buyers who spend a fixed
budget and name no maximum price, profit rises with the ask without limit, so without the hold the ask
ratchets up each year; and a seller that sells next to nothing at an ask above the hold comes down to it
at once, since a market in which it is idle tells it nothing about a price above what undercutting rivals
could ask.
"""
import dataclasses
import math
from typing import List, Optional, Sequence

from sim.constants import declare

from . import crowd_offers, entry_trial, goods_market, market_curves, seller_pricing
from .producers import UNSOLD_ASK_MARKDOWN_SHARE, expected_output_prices, live_input_prices, live_wages
from .types import EDGE_EXTERNAL, Bid, Offer

IDLE_SALE_SHARE = declare(
    "IDLE_SALE_SHARE", 0.01, kind="temporary_heuristic", unit="share of its offer a seller sells at its ask",
    source=None, confidence="D",
    why="A seller that sells less than this share of what it offers at its ask is idle: its ask is above what "
        "any real buyer pays, so it comes down to cost times the substitution markup at once instead of "
        "marking down a share a year. Where idle begins has no measured basis.")


def merged_bids(bids: Sequence[Bid], good: str) -> List[Bid]:
    """The buyers' schedules merged where they share a reference price, elasticity and ceiling (as the
    book's summary does), the external edge's own bids kept as they are."""
    outside = [bid for bid in bids if bid.buyer == EDGE_EXTERNAL]
    return market_curves.bids_of(market_curves.summarize(bids, []), good) + outside


def unit_cost(setup, record, view, offer: Offer) -> Optional[float]:
    """What one unit of the offer's good costs its producer to make at today's prices (infinite when that
    cannot be priced); None for a seller that is not a producer."""
    producer = record.producers.get(offer.seller)
    if producer is None:
        return None
    recipe = setup.recipes[producer.recipe_id]
    return entry_trial.full_cost_per_unit(
        recipe, offer.good, expected_output_prices(producer, recipe, view), live_input_prices(producer, recipe, view),
        live_wages(producer, recipe, view), 0.0, producer.land_rent_per_run, producer.yield_factor)


def unit_value(offer: Offer, cost: float) -> float:
    """What one more unit of the offer's good is worth to its producer unsold."""
    return min(cost, max(offer.reservation_price, 0.0))


def substitution_markup(setup, offer: Offer) -> float:
    """The ratio of price to cost a seller can charge when buyers substitute toward other goods meeting the
    same need at the basket's elasticity of substitution (the constant-elasticity monopolist's markup);
    unbounded when buyers do not substitute more than one for one."""
    elasticity = setup.basket_for(offer.tile).substitution
    return elasticity / (elasticity - 1.0) if elasticity > 1.0 else math.inf


def stands_for_many(record, offer: Offer) -> bool:
    """True for a producer that stands for several independent workshops (entry.py joins each newcomer to
    the tile's producer): each workshop takes the price, so the aggregate offers its units at their
    price-taking reservations and does not withhold supply against its residual demand."""
    producer = record.producers.get(offer.seller)
    return producer is not None and producer.workshops > 1


def strategic_offers(setup, record, view, bids: Sequence[Bid], offers: Sequence[Offer],
                     last_price: Optional[float]) -> List[Offer]:
    """`offers` with each moving producer's reservation re-chosen, in agent order."""
    offers = list(offers)
    if not bids or not offers:
        return offers
    good = offers[0].good
    book = merged_bids(bids, good)
    buyers = goods_market.Buyers(book, last_price)
    for index in sorted(range(len(offers)), key=lambda each: (offers[each].seller, offers[each].tile)):
        offer = offers[index]
        if offer.quantity <= 0.0:
            continue
        cost = unit_cost(setup, record, view, offer)
        if cost is None:
            continue
        value = unit_value(offer, cost)
        rivals = offers[:index] + offers[index + 1:]
        ask = max(offer.reservation_price, 0.0)
        crowd = stands_for_many(record, offer)
        # a crowd of price takers earns no markup: the dearest ask it holds when nothing sells is its cost
        limit = cost if crowd else cost * substitution_markup(setup, offer)
        if ask > limit and math.isfinite(limit):
            sold, _price = seller_pricing.sold_and_price(book, rivals, offer, ask, last_price, buyers)
            if sold < IDLE_SALE_SHARE * offer.quantity:
                offers[index] = dataclasses.replace(offer, reservation_price=limit)
                continue
        if crowd:
            # unsold stock at an ask above cost: the crowd marks down by the share of its offer left unsold, never below cost
            if ask > cost and math.isfinite(cost):
                sold, _price = seller_pricing.sold_and_price(book, rivals, offer, ask, last_price, buyers)
                unsold_share = 1.0 - sold / offer.quantity if offer.quantity > 0.0 else 0.0
                if unsold_share > 0.0:     # close the gap to cost by the share of the offer left unsold
                    offers[index] = dataclasses.replace(offer, reservation_price=ask - unsold_share * (ask - cost))
            continue
        step = UNSOLD_ASK_MARKDOWN_SHARE * (ask if ask > 0.0 else max(last_price or 0.0, 0.0))
        floor = ask * (1.0 - UNSOLD_ASK_MARKDOWN_SHARE)
        choice = seller_pricing.best_reservation(
            book, rivals, offer, value, last_price, ceiling=min(ask + step, max(limit, floor)), floor=floor,
            current=ask, buyers=buyers)
        if choice is not None:
            offers[index] = dataclasses.replace(offer, reservation_price=choice)
    return [piece for offer in offers for piece in
            (crowd_offers.schedule(offer) if stands_for_many(record, offer) else (offer,))]
