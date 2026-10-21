"""What a thinly traded market remembers: a traded price relaxed toward what the good costs to make.

A market with buyers and no sellers reports a cost-covering quote instead (market_quote.py); a market that
traded only a sliver of what is usual keeps its traded price but moves it part of the way to the cost.
"""
from typing import Optional

from sim.constants import declare

from .market_memory_asks import REPRESENTATIVE_TRADE_SHARE

NO_OFFER_MEMORY_SHARE = declare(
    "NO_OFFER_MEMORY_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the gap to a year's quote closed in a year in which the market did not trade", source=None,
    confidence="D", retire="Complaints/642-a-market-shows-and-uses-a-price-where-nothing-traded.md",
    why="Planners who find nothing traded learn what the posted bids, asks or making cost say, partway in a "
        "year: a cost-covering quote taken whole would tell every maker its runs pay and no maker would "
        "ever leave. How fast that news travelled is not modelled; a planner that reads the quote itself "
        "(MarketView.quote_kind) needs no speed.")


def price_toward_quote(old: Optional[float], quote_price: float) -> float:
    """The planning price after a year with no trade: part of the way from the old one to the quote's
    price (the quote itself where nothing was remembered)."""
    return quote_price if old is None else old + NO_OFFER_MEMORY_SHARE * (quote_price - old)


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
