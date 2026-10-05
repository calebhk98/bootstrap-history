"""What a market with buyers and no sellers remembers: the price moves toward what the good costs to make.

A market nobody offered in never trades, so its remembered price would stay wherever it was last set.
Households share their spending by those prices, so a good nobody sells at a stale low price draws the
budget away from foods that are on offer, and people go hungry with money in hand; newcomers judge the
market by the same price and never come. The cost of making the good at the live prices and wages is
what a seller would have to ask, so the memory follows it part of the way, up or down.
"""
from typing import Optional

from sim.constants import declare

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
