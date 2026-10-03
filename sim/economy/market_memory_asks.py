"""What a market with sellers and no buyers remembers: the price drifts down toward the lowest ask.

A market where nothing was bid never trades, so its remembered price would stay wherever it was
last set, and buyers who plan from that price find their runs do not pay and never bid. Sellers
mark their asks down on unsold stock (producers.py), so the lowest ask is the one thing such a
market shows; the memory follows it part of the way down.
"""
from typing import Optional, Sequence

from sim.constants import declare

from .goods_market_demand import DemandSchedule
from .types import Bid, Offer

NO_BID_MEMORY_SHARE = declare(
    "NO_BID_MEMORY_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the gap to the lowest ask closed in a year with offers and no bids", source=None,
    confidence="D",
    why="Buyers plan from a remembered price and a market nobody bids in gives it nothing new. The "
        "lowest ask is what sellers are willing to take, so the memory moves toward it, partway so "
        "one seller's low ask does not become the price. Real buyers would look at sellers' posted "
        "prices; the economy has no such listing, so the speed is a placeholder.")


def has_no_bids(bids: Sequence[Bid]) -> bool:
    return not any(bid.budget > 0.0 for bid in bids)


def price_after_no_bids(old: Optional[float], bids: Sequence[Bid], offers: Sequence[Offer]) -> Optional[float]:
    """The remembered price after a year with offers and no bids: part of the way down to the lowest
    ask. None when the market had bids or no offers, when nothing was remembered, or when the ask is
    not below the memory (an ask above the remembered price is no evidence the price rose)."""
    if old is None or not offers or not has_no_bids(bids):
        return None
    lowest_ask = min(offer.reservation_price for offer in offers)
    if not lowest_ask > 0.0 or lowest_ask >= old:
        return None
    return old + NO_BID_MEMORY_SHARE * (lowest_ask - old)


RESUMED_TRADE_MEMORY_SHARE = declare(
    "RESUMED_TRADE_MEMORY_SHARE", 0.25, kind="temporary_heuristic",
    unit="share of the gap to the cleared price closed when trade resumes after years without bids",
    source=None, confidence="D",
    why="The first trade after years with nobody bidding is one buyer's price in a market that had no "
        "buyers, and the market's usual volume has run down to nothing, so the volume rule would adopt "
        "it whole. Buyers and sellers who watched the market go quiet weigh it against the price it "
        "had drifted to. Unmeasured.")


def note_bids(memory, key: str, bids: Sequence[Bid], offers: Sequence[Offer]) -> int:
    """Count the years a market with offers has had nobody bidding; returns the count before this year."""
    before = memory.years_without_bids.get(key, 0)
    if offers and has_no_bids(bids):
        memory.years_without_bids[key] = before + 1
    else:
        memory.years_without_bids.pop(key, None)
    return before


def note_offers(memory, key: str, bids: Sequence[Bid], offers: Sequence[Offer]) -> int:
    """Count the years a market with bids has had no seller; returns the count before this year."""
    before = memory.years_without_offers.get(key, 0)
    if not any(offer.quantity > 0.0 for offer in offers) and not has_no_bids(bids):
        memory.years_without_offers[key] = before + 1
    else:
        memory.years_without_offers.pop(key, None)
    return before


def price_after_resumed_trade(old: Optional[float], volume_rule_price: float, years_without_bids: int) -> float:
    """After trade resumes, the remembered price moves only part of the way from the price the quiet
    market drifted to."""
    if old is None or years_without_bids <= 0:
        return volume_rule_price
    return old + RESUMED_TRADE_MEMORY_SHARE * (volume_rule_price - old)


def wanted_at(bids: Sequence[Bid], price: Optional[float]) -> float:
    """What the buyers would have taken at a price (budgets and ceilings applied); zero without a price."""
    if not price or price <= 0.0 or not bids:
        return 0.0
    return DemandSchedule(sorted(bids, key=lambda bid: (bid.priority, bid.buyer, bid.tile))).total_at(price)
