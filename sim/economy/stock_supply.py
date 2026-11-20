"""What a producer will take for its stock, unit by unit, under the clearing rule set: a supply curve over the price.

A producer keeps a stock against its expected sales (`inventory.target_stock`). Holding exactly that stock it is content
to sell a unit at the price it expects. Each unit it holds beyond that stock it lets go for less, the more it holds the
less; each unit that would take it under that stock it lets go only for more. Cut into a few offers, this gives the
market a supply that rises with the price inside the year, so the price where demand meets it moves a little when
demand moves a little, a glut shows in the price at once, and a producer whose sales and stock are what it expected
sells at the price it expected."""
import math
from typing import List, Sequence, Tuple

from sim.constants import declare

from . import inventory
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
STOCK_SUPPLY_OFFERS = declare(
    "STOCK_SUPPLY_OFFERS", 8, kind="temporary_heuristic", unit="offers a producer's stock of a good is cut into",
    source=None, confidence="D",
    retire="no complaint covers it; retired when a market takes a seller's supply as a curve and not as steps",
    why="How finely the supply curve is cut into offers; the marginal offers share a sale pro rata, so a few are enough.")


def reservations_by_stock_level(held: float, target: float, content_price: float, offers: int = STOCK_SUPPLY_OFFERS,
                                slope: float = STOCK_PRICE_SLOPE) -> List[Tuple[float, float]]:
    """[(quantity, reservation price)] for a stock of `held` units cut into equal parts from the top of the pile down:
    the part whose middle unit leaves the seller with a stock of `level` is offered at `content_price` (what it takes
    holding exactly its target) times e to the power `slope` times how far that level is under the target as a share of
    it (over the target: negative), so the reservation is `content_price` at the target, falls smoothly and stays
    above nothing however large the pile, and rises as the stock is drawn down."""
    if held <= 0.0 or target <= 0.0:
        return []
    part = held / offers
    cut = []
    for index in range(offers):
        level = held - (index + 0.5) * part          # the stock left once the middle unit of this part is sold
        cut.append((part, content_price * math.exp(slope * (1.0 - level / target))))
    return cut


def content_price(expected_price: float, posted_reservation: float, carrying_value: float) -> float:
    """What a seller takes for a unit when it holds exactly its target stock: the price it expects, lowered by the share
    its posted reservation stands under the plain value of carrying a unit a year (a seller short of cash posts less,
    `inventory.distressed_reservation`)."""
    if carrying_value <= 0.0 or posted_reservation >= carrying_value:
        return expected_price
    return expected_price * max(0.0, posted_reservation) / carrying_value


def offers_by_stock_level(setup, record, view, good: str, offers: Sequence[Offer]) -> List[Offer]:
    """`offers` with each producer's offer of `good` cut into offers along its supply curve. Left as posted: other
    sellers' offers, and a producer's where it has no expected price or sales for the good, or a unit cannot be carried
    a year (a perishable, a waste product: it goes at any price). The order of the sellers is kept."""
    spoilage = setup.specs[good].spoilage_per_year if good in setup.specs else 0.0
    cut: List[Offer] = []
    for offer in offers:
        producer = record.producers.get(offer.seller) if offer.quantity > 0.0 else None
        expected = None if producer is None else producer.expected_prices.get(good)
        made = 0.0 if producer is None else setup.recipes[producer.recipe_id].outputs.get(good, 0.0) * producer.yield_factor
        target = 0.0 if producer is None else inventory.target_stock(producer.expected_sales) * made
        if expected is None or expected <= 0.0 or target <= 0.0:
            cut.append(offer)
            continue
        currency = view.currency_of(offer.area)
        carrying = inventory.holding_reservation(expected, view.interest_rate(currency) or 0.0, spoilage,
                                                 STORAGE_COST_PER_UNIT * view.opening_wage_level(currency))
        if carrying <= 0.0:
            cut.append(offer)
            continue
        content = content_price(expected, offer.reservation_price, carrying)
        cut.extend(Offer(offer.seller, offer.good, offer.area, offer.tile, quantity, reservation)
                   for quantity, reservation in reservations_by_stock_level(offer.quantity, target, content))
    return cut
