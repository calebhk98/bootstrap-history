"""The producers' offers in one market, re-chosen against that market's book before it clears.

Each producer in turn (by agent id) reads the buyers' schedules and the other sellers' current offers and,
if its own offer moves the clearing price (seller_pricing.py), asks the reservation that maximises its
profit; a producer that does not move the price keeps the reservation `producers.offers` gave it. What a
unit is worth to the seller unsold is the cheaper of replacing it (its variable cost per unit) and holding
it (its price-taking reservation), so a seller never prices below what a unit costs it to make or keep.
A seller that moves the price may also raise its ask above the price-taking one, which holds units back
(restraint) when the dearer, smaller sale earns more. A change either way is bounded by the share a seller
already marks its ask down in a year (UNSOLD_ASK_MARKDOWN_SHARE), so an ask moves over the years as the
book changes and never jumps in one; an ask raised past what buyers pay goes unsold and is marked down
again by the producer's own rule.
"""
import dataclasses
from typing import List, Optional, Sequence

from . import entry_trial, market_curves, seller_pricing
from .producers import UNSOLD_ASK_MARKDOWN_SHARE, expected_output_prices, live_input_prices, live_wages
from .types import EDGE_EXTERNAL, Bid, Offer


def merged_bids(bids: Sequence[Bid], good: str) -> List[Bid]:
    """The buyers' schedules merged where they share a reference price, elasticity and ceiling (as the
    book's summary does), the external edge's own bids kept as they are."""
    outside = [bid for bid in bids if bid.buyer == EDGE_EXTERNAL]
    return market_curves.bids_of(market_curves.summarize(bids, []), good) + outside


def unit_value(setup, record, view, offer: Offer) -> Optional[float]:
    """What one more unit of the offer's good is worth to its producer unsold; None for a seller that is
    not a producer."""
    producer = record.producers.get(offer.seller)
    if producer is None:
        return None
    recipe = setup.recipes[producer.recipe_id]
    cost = entry_trial.full_cost_per_unit(
        recipe, offer.good, expected_output_prices(producer, recipe, view), live_input_prices(producer, recipe, view),
        live_wages(producer, recipe, view), 0.0, producer.land_rent_per_run, producer.yield_factor)
    return min(cost, max(offer.reservation_price, 0.0))


def strategic_offers(setup, record, view, bids: Sequence[Bid], offers: Sequence[Offer],
                     last_price: Optional[float]) -> List[Offer]:
    """`offers` with each moving producer's reservation re-chosen, in agent order."""
    offers = list(offers)
    if not bids or not offers:
        return offers
    good = offers[0].good
    book = merged_bids(bids, good)
    for index in sorted(range(len(offers)), key=lambda each: (offers[each].seller, offers[each].tile)):
        offer = offers[index]
        value = unit_value(setup, record, view, offer)
        if value is None or offer.quantity <= 0.0:
            continue
        rivals = offers[:index] + offers[index + 1:]
        ask = max(offer.reservation_price, 0.0)
        step = UNSOLD_ASK_MARKDOWN_SHARE * (ask if ask > 0.0 else max(last_price or 0.0, 0.0))
        choice = seller_pricing.best_reservation(
            book, rivals, offer, value, last_price, ceiling=ask + step,
            floor=ask * (1.0 - UNSOLD_ASK_MARKDOWN_SHARE), current=ask)
        if choice is not None:
            offers[index] = dataclasses.replace(offer, reservation_price=choice)
    return offers
