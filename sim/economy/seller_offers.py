"""The producers' offers in one market, re-priced before it clears.

Each producer with units to sell reads the other sellers' asks and the market's size and chooses its reservation as
Eurace@Unibi's firm sets its price (price_setting.py, after Market_Research/Firm_market_research_functions.c, Firm_set_price):
the price on a grid around its own that earns most over the year, sales capped by the units it holds. What a unit is
worth to the seller unsold is the cheaper of replacing it (its variable cost per unit) and holding it (its
price-taking reservation), so a seller never prices below what a unit costs it to make or keep. A producer that
stands for several workshops (Producer.workshops above one) is not a seller but a crowd of price takers: it keeps the
price-taking reservation and neither searches nor raises, and as a rival it counts once per workshop. A seller whose
market has no sales on record keeps its reservation; one whose reservation is nothing but whose good has a making cost
opens at the price it expects (opened_ask), never at nothing. The chosen
ask is held inside a band above the seller's unit cost (ask_band_multiple), and a seller whose ask goes unsold is
brought down to what sells by unsold_search.py. The reservation itself moves between years with the seller's stock
against its target (ask_adjust.py), which is the grid's centre.
"""
import dataclasses
import math
from typing import List, Optional, Sequence, Tuple

from . import entry_trial, price_setting
from . import unit_cost as run_cost
from .ask_adjust import ASK_BAND_CEILING, band_edge
from .market_memory import market_key
from .producers import expected_output_prices, live_input_prices, live_wages
from .types import Bid, Offer


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


def input_share_of_cost(setup, record, view, offer: Offer) -> float:
    """The share of a run's variable cost the producer pays for bought inputs (none for a seller that is not a
    producer or whose cost cannot be priced): the band above cost marks up only the rest (ask_adjust.band_edge)."""
    producer = record.producers.get(offer.seller)
    if producer is None:
        return 0.0
    recipe = setup.recipes[producer.recipe_id]
    inputs = live_input_prices(producer, recipe, view)
    variable = run_cost.variable_cost_per_run(recipe, inputs, live_wages(producer, recipe, view), producer.land_rent_per_run)
    return run_cost.input_cost_per_run(recipe, inputs) / variable if math.isfinite(variable) and variable > 0.0 else 0.0


def opened_ask(reservation: float, cost: Optional[float], expected_price: Optional[float], limit: float) -> Optional[float]:
    """The ask a seller whose reservation is nothing opens at: a good that costs something to make is not given away, so
    the seller asks the price it expects (held to the top of the band) and the unsold search brings it down to what
    sells. None when the reservation is positive (it is the ask), the good has no cost that can be priced (a waste
    product, which the market places at its lowest price), or the seller has no price it expects."""
    if reservation > 0.0 or cost is None or not math.isfinite(cost) or cost <= 0.0:
        return None
    if expected_price is None or not math.isfinite(expected_price) or expected_price <= 0.0:
        return None
    return min(expected_price, limit)


def expected_ask(reservation: float, expected_price: Optional[float], stock: float, expected_sales: float) -> float:
    """The ask of a seller whose stock is within the year's sales it expects: the price it expects (which ask_adjust.py
    already keeps from climbing past the band), not
    the lower price at which it would carry a unit to next year, since every unit is expected to sell this year. A seller
    asking its walk-away price would see that price back as the market's and expect less each year. The reservation
    stands when it is higher, when the stock is more than the sales expected, or when there is no expectation."""
    if expected_price is None or not math.isfinite(expected_price) or expected_sales <= 0.0 or stock > expected_sales:
        return reservation
    return max(reservation, expected_price)


def unit_value(offer: Offer, cost: float) -> float:
    """What one more unit of the offer's good is worth to its producer unsold."""
    return min(cost, max(offer.reservation_price, 0.0))


def substitution_markup(setup, offer: Offer) -> float:
    """The ratio of price to cost a seller can charge when buyers substitute toward other goods meeting the
    same need at the basket's elasticity of substitution (the constant-elasticity monopolist's markup);
    where buyers do not substitute more than one for one the stated band (ASK_BAND_CEILING) stands in."""
    elasticity = setup.basket_for(offer.tile).substitution
    return elasticity / (elasticity - 1.0) if elasticity > 1.0 else ASK_BAND_CEILING


def ask_band_multiple(setup, offer: Offer) -> float:
    """The most, as a multiple of a unit's cost, any seller's ask may be: the derived substitution markup,
    never past ASK_BAND_CEILING, so inelastic demand gives a finite ask."""
    return min(substitution_markup(setup, offer), ASK_BAND_CEILING)


def stands_for_many(record, offer: Offer) -> bool:
    """True for a producer that stands for several independent workshops (entry.py joins each newcomer to
    the tile's producer): each workshop takes the price, so the aggregate offers its units at their
    price-taking reservations and does not withhold supply against its residual demand."""
    producer = record.producers.get(offer.seller)
    return producer is not None and producer.workshops > 1


def strategic_offers(setup, record, view, bids: Sequence[Bid], offers: Sequence[Offer],
                     last_price: Optional[float], costs: Optional[dict] = None) -> List[Offer]:
    """`offers` with each moving producer's reservation re-chosen, in agent order. A `costs` dict receives
    each offer's `unit_cost` by (seller, tile), for the unsold search of the same market to read."""
    original = list(offers)
    offers = list(offers)
    if not bids or not offers:
        return offers
    for index in sorted(range(len(offers)), key=lambda each: (offers[each].seller, offers[each].tile)):
        offer = offers[index]
        if offer.quantity <= 0.0:
            continue
        cost = unit_cost(setup, record, view, offer)
        if costs is not None:
            costs[(offer.seller, offer.tile)] = cost
        if cost is None:
            continue
        if offer.reservation_price <= 0.0:       # a perishable or a distressed holder: it asks a price, never nothing
            producer = record.producers[offer.seller]
            recipe = setup.recipes[producer.recipe_id]
            limit = (band_edge(cost, input_share_of_cost(setup, record, view, offer), ask_band_multiple(setup, offer))
                     if math.isfinite(cost) else math.inf)
            opened = opened_ask(offer.reservation_price, cost,
                                expected_output_prices(producer, recipe, view).get(offer.good), limit)
            if opened is not None:
                offers[index] = dataclasses.replace(offer, reservation_price=opened)
                continue
        if stands_for_many(record, offer):
            # a crowd of price takers asks what it expects for stock it expects to sell; unsold_search.py lowers it to what sells
            producer = record.producers[offer.seller]
            recipe = setup.recipes[producer.recipe_id]
            asked = expected_ask(offer.reservation_price, expected_output_prices(producer, recipe, view).get(offer.good),
                                 offer.quantity, producer.expected_sales * recipe.outputs.get(offer.good, 0.0))
            if asked != offer.reservation_price:
                offers[index] = dataclasses.replace(offer, reservation_price=asked)
            continue
        value = unit_value(offer, cost)
        size = market_size(record, offer)
        if offer.reservation_price <= 0.0 or size is None:
            continue      # a seller that sells at any price, or a market with no sales to judge by, keeps its ask
        limit = (band_edge(cost, input_share_of_cost(setup, record, view, offer), ask_band_multiple(setup, offer))
                 if math.isfinite(cost) else math.inf)
        choice = price_setting.best_price(offer.reservation_price, value, size, rivals_of(record, original, index), offer.quantity,
                                          value, max(limit, value))
        if choice != offer.reservation_price:
            offers[index] = dataclasses.replace(offer, reservation_price=choice)
    return offers


def market_size(record, offer: Offer) -> Optional[float]:
    """What the whole market bought a year, plus what its buyers wanted and did not get, read off the market's memory
    (the smoothed volume, with no series to fit a trend to: Eurace@Unibi, Market_Research/Firm_market_research_functions.c,
    Firm_set_market_research_data_pricing, takes the mean of its market sizes when it has too few for a regression); None
    when the market has no history."""
    key = market_key(offer.good, offer.area)
    usual = record.memory.volume_weights.get(key)
    if usual is None:
        return None
    return usual + record.unmet.get(key, 0.0)


def rivals_of(record, offers: Sequence[Offer], index: int) -> List[Tuple[float, float]]:
    """(ask, number of workshops) of every other seller in the market with units to sell, as the book stood before any
    seller moved (Eurace@Unibi's households choose among the prices last seen), so the answer does not depend on the order
    sellers are taken in."""
    rivals = []
    for other, each in enumerate(offers):
        if other != index and each.quantity > 0.0 and each.reservation_price > 0.0:
            producer = record.producers.get(each.seller)
            rivals.append((each.reservation_price, float(producer.workshops) if producer is not None else 1.0))
    return rivals
