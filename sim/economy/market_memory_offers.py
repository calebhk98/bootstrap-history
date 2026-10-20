"""What a market with buyers and no sellers remembers: the price moves toward what the good costs to make.

A market nobody offered in never trades, so its remembered price would stay wherever it was last set.
Households share their spending by those prices, so a good nobody sells at a stale low price draws the
budget away from foods that are on offer, and people go hungry with money in hand; newcomers judge the
market by the same price and never come. The cost of making the good at the live prices and wages is
what a seller would have to ask, so the memory follows it part of the way, up or down.
"""
from typing import Optional

from sim.constants import declare

from .market_memory_asks import REPRESENTATIVE_TRADE_SHARE

NO_OFFER_MEMORY_SHARE = declare(
    "NO_OFFER_MEMORY_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the gap to the cost of making closed in a year with bids and no offers", source=None,
    confidence="D",
    why="Pairs with NO_BID_MEMORY_SHARE: buyers who find nothing on offer learn what the good would cost "
        "from traders and makers elsewhere, partway in a year. How fast that news travelled is not "
        "modelled.")


def price_after_no_offers(old: Optional[float], cost: Optional[float]) -> Optional[float]:
    """The remembered price after a year with bids and no offers: part of the way to the cost of making
    the good. None when nothing was remembered or the good cannot be made."""
    if old is None or cost is None or cost <= 0.0:
        return None
    return old + NO_OFFER_MEMORY_SHARE * (cost - old)


def price_after_thin_trade(price: Optional[float], cost: Optional[float], quantity: float,
                           usual_volume: float) -> Optional[float]:
    """A remembered price relaxed toward the cost of making the good when the year's trade fell short of a
    representative trade (REPRESENTATIVE_TRADE_SHARE of the market's usual volume): at the no-offer rate,
    scaled by how far short, and only downward: a price above what the good costs to make finds no
    buyers, while a price below it is the no-offer rule's business. Measured against the usual volume, not what buyers want, so a market short of
    supply is not taken for a dead one. A market trading representatively, or a good with no cost or no
    usual volume, keeps its price."""
    if price is None or cost is None or cost <= 0.0 or cost >= price or usual_volume <= 0.0:
        return price
    shortfall = max(0.0, 1.0 - quantity / (REPRESENTATIVE_TRADE_SHARE * usual_volume))
    return price + NO_OFFER_MEMORY_SHARE * shortfall * (cost - price)


PRICE_OVER_MAKING_COST_LIMIT = declare(
    "PRICE_OVER_MAKING_COST_LIMIT", 4.0, kind="temporary_heuristic",
    unit="times the cost of making a good", source=None, confidence="D",
    why="Buyers with a fixed want and few sellers bid a thin market up year on year (a cart for a merchant's "
        "wear, brick, a joint by-product nobody makes), and no seller or entrant is modelled to answer the "
        "scarcity rent. In the long run a good sells for about what it costs to make, so the remembered price "
        "is held within a multiple of that cost; how large a rent lasts has no measured basis.",
    retire="Complaints/473: entry into a scarce good's making answers its rent")


def price_within_making_cost(price: float, cost: Optional[float]) -> float:
    """A remembered price held to PRICE_OVER_MAKING_COST_LIMIT times the cost of making the good. A good with
    no cost (nobody can make it) is not capped here: it has no cost to bound it by."""
    if cost is None or cost <= 0.0:
        return price
    return min(price, PRICE_OVER_MAKING_COST_LIMIT * cost)
