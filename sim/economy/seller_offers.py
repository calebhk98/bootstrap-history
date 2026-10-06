"""The producers' offers in one market, re-chosen against that market's book before it clears.

Each producer in turn (by agent id) reads the buyers' schedules and the other sellers' current offers and,
if its own offer moves the clearing price (seller_pricing.py), asks the reservation that maximises its
profit; a producer that does not move the price keeps the reservation `producers.offers` gave it. What a
unit is worth to the seller unsold is the cheaper of replacing it (its variable cost per unit) and holding
it (its price-taking reservation), so a seller never prices below what a unit costs it to make or keep.
A producer stands for every workshop running its recipe on its tile, and those workshops cannot hold goods
back together, so a producer may cut its ask below the price-taking one but never raise it
(temporary heuristic: restraint needs a firm, not an aggregate of competing workshops). The cut is
bounded by the share a seller already marks its ask down in a year (UNSOLD_ASK_MARKDOWN_SHARE), so a
producer's price falls over the years as its capacity grows and never collapses in one.
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
        choice = seller_pricing.best_reservation(
            book, rivals, offer, value, last_price, ceiling=max(offer.reservation_price, 0.0),
            floor=max(offer.reservation_price, 0.0) * (1.0 - UNSOLD_ASK_MARKDOWN_SHARE))
        if choice is not None:
            offers[index] = dataclasses.replace(offer, reservation_price=choice)
    return offers
