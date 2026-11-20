"""What a producer will take for its stock, unit by unit, under the clearing rule set: a supply curve over the price.

A producer keeps a stock against its expected sales (`inventory.target_stock`). Holding exactly that stock it is content
to sell a unit at the price it expects. Each unit it holds beyond that stock it lets go for less, the more it holds the
less, down to what a unit is worth to it kept for next year (the reservation it posted, `inventory.holding_reservation`)
and no lower; each unit that would take it under that stock it lets go only for more. This gives the
market a supply that rises with the price inside the year, so the price where demand meets it moves a little when
demand moves a little, a glut shows in the price at once and beyond that stays in stock, and a producer whose sales and
stock are what it expected sells at the price it expected. A good that cannot be kept has no stock to read: its curve is
`fresh_supply.FreshCurve`."""
import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from sim.constants import declare

from . import inventory
from .fresh_supply import FreshCurve
from .producers import STORAGE_COST_PER_UNIT
from .types import Offer

STOCK_PRICE_SLOPE = declare(
    "STOCK_PRICE_SLOPE", 0.25, kind="temporary_heuristic",
    unit="share of the expected price a seller asks more (less) for a unit when its stock is a whole target under (over) its target",
    source=None, confidence="D",
    retire="Complaints/473: a holder's own valuation of its buffer (the cost of running out against the cost of carrying) gives the slope",
    why="How steeply a seller's reservation rises as its stock is drawn down. A flat one makes the price jump between the "
        "carrying value and the buyers' ceiling whenever sales differ a hair from output; this slope spreads that over "
        "the buffer. Not fitted.")
@dataclass(frozen=True)
class StockCurve:
    """One producer's supply of a good out of its stock: the offer it posted (every unit it holds), the stock it means to
    keep, the price it takes for a unit when it holds exactly that stock, and the price under which it keeps every unit
    for next year."""
    offer: Offer
    target: float
    content_price: float
    floor_price: float = 0.0

    def level_at(self, price: float) -> float:
        """The stock the seller keeps at a price: its target at the content price, less as the price rises and more as it
        falls, by `STOCK_PRICE_SLOPE` (the price is the content price times e to the slope times the share of the target the
        stock is under it); all of it under the floor price."""
        if price <= 0.0 or price < self.floor_price:
            return math.inf
        return self.target * (1.0 - math.log(price / self.content_price) / STOCK_PRICE_SLOPE)

    def supply_at(self, price: float) -> float:
        """Units the seller lets go at a price: what it holds beyond the stock it keeps at it, none to all of the offer."""
        return max(0.0, min(self.offer.quantity, self.offer.quantity - self.level_at(price)))

    @property
    def lowest_price(self) -> float:
        """The price under which the seller lets nothing go: where its curve reaches nothing, or its floor price if higher."""
        return max(self.floor_price, self.content_price * math.exp(STOCK_PRICE_SLOPE * (1.0 - self.offer.quantity / self.target)))

    @property
    def highest_price(self) -> float:
        """The price at which the seller has let everything go."""
        return max(self.floor_price, self.content_price * math.exp(STOCK_PRICE_SLOPE))

    @property
    def asking_price(self) -> float:
        """What the seller asks for a unit nobody bought: the least it lets one go for."""
        return self.lowest_price

    def offer_at(self, price: float) -> Offer:
        """The seller's offer in a market that clears at `price`: the units it lets go at it, at that price (at its
        highest price where it lets everything go under `price`)."""
        offer = self.offer
        return Offer(offer.seller, offer.good, offer.area, offer.tile, self.supply_at(price), min(price, self.highest_price))


def content_price(expected_price: float, posted_reservation: float, carrying_value: float) -> float:
    """What a seller takes for a unit when it holds exactly its target stock: the price it expects, lowered by the share
    its posted reservation stands under the plain value of carrying a unit a year (a seller short of cash posts less,
    `inventory.distressed_reservation`)."""
    if carrying_value <= 0.0 or posted_reservation >= carrying_value:
        return expected_price
    return expected_price * max(0.0, posted_reservation) / carrying_value


def curves_and_posted(setup, record, view, good: str, offers: Sequence[Offer]) -> Tuple[list, List[Offer]]:
    """(the producers' supply curves for `good`, the offers that stay as posted). A producer's curve is a `StockCurve`
    where a unit can be carried a year and it expects sales to hold a stock against, a `FreshCurve` where a unit cannot be
    carried. Posted as they are: other sellers' offers, and a producer's where it has no expected price for the good or
    (for a good that keeps) no expected sales. The order of the sellers is kept within each list."""
    spoilage = setup.specs[good].spoilage_per_year if good in setup.specs else 0.0
    curves: List[StockCurve] = []
    posted: List[Offer] = []
    for offer in offers:
        producer = record.producers.get(offer.seller) if offer.quantity > 0.0 else None
        expected = None if producer is None else producer.expected_prices.get(good)
        made = 0.0 if producer is None else setup.recipes[producer.recipe_id].outputs.get(good, 0.0) * producer.yield_factor
        target = 0.0 if producer is None else inventory.target_stock(producer.expected_sales) * made
        if expected is None or expected <= 0.0:
            posted.append(offer)
            continue
        currency = view.currency_of(offer.area)
        carrying = inventory.holding_reservation(expected, view.interest_rate(currency) or 0.0, spoilage,
                                                 STORAGE_COST_PER_UNIT * view.opening_wage_level(currency))
        if carrying <= 0.0:
            curves.append(FreshCurve(offer, expected))
            continue
        content = content_price(expected, offer.reservation_price, carrying)
        if target <= 0.0 or content <= 0.0:
            posted.append(offer)
            continue
        curves.append(StockCurve(offer, target, content, max(0.0, offer.reservation_price)))
    return curves, posted
