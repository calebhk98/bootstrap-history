"""What a market that did not trade reports: a quote, never a price.

A price is one both sides agreed to trade at, so a market has one only for a year in which it traded. A
market that did not trade shows the figure that comes from what is actually posted, named as what it is:
the best unfilled bid when buyers bid but every ask was above it, the lowest unfilled ask when nobody
bid, and (where the caller knows what a unit costs to make) a cost-covering quote when buyers bid and
nobody offered.
"""
import math
from typing import Optional, Sequence

from .types import QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING, QUOTE_LOWEST_UNFILLED_ASK, Bid, Offer, Quote


def best_unfilled_bid(bids: Sequence[Bid]) -> Optional[float]:
    """The most any buyer with money to spend would have paid; None when none names a finite maximum."""
    ceilings = [bid.maximum_price for bid in bids if bid.budget > 0.0 and math.isfinite(bid.maximum_price)
                and bid.maximum_price > 0.0]
    return max(ceilings) if ceilings else None


def lowest_unfilled_ask(offers: Sequence[Offer]) -> Optional[float]:
    asks = [offer.reservation_price for offer in offers if offer.quantity > 0.0 and offer.reservation_price > 0.0]
    return min(asks) if asks else None


def no_trade_quote(bids: Sequence[Bid], offers: Sequence[Offer], cost: Optional[float] = None) -> Optional[Quote]:
    """The quote of a market where nothing traded; None when it posts nothing to quote."""
    asks = lowest_unfilled_ask(offers)
    anyone_bid = any(bid.budget > 0.0 for bid in bids)
    bid_price = best_unfilled_bid(bids)
    if asks is None:
        if cost is not None and cost > 0.0 and anyone_bid:
            return Quote(QUOTE_COST_COVERING, cost)
        return Quote(QUOTE_BEST_UNFILLED_BID, bid_price) if bid_price is not None else None
    if bid_price is not None and bid_price < asks:
        return Quote(QUOTE_BEST_UNFILLED_BID, bid_price)
    if anyone_bid:
        return None      # an ask at or under a bid that still did not trade says nothing about a price
    return Quote(QUOTE_LOWEST_UNFILLED_ASK, asks)
