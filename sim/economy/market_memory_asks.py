"""What a market remembers across years of thin or resumed trade, and how long it has gone without bids or
offers. A market with sellers and no buyers reports the lowest unfilled ask as a quote (market_quote.py)."""
import math
from typing import Optional, Sequence

from sim.constants import declare

from .goods_market import quantity_at
from .types import EDGE_EXTERNAL, Bid, Offer

def has_no_bids(bids: Sequence[Bid]) -> bool:
    return not any(bid.budget > 0.0 for bid in bids)


RESUMED_TRADE_MEMORY_SHARE = declare(
    "RESUMED_TRADE_MEMORY_SHARE", 0.25, kind="temporary_heuristic",
    unit="share of the gap to the cleared price closed when trade resumes after years without bids",
    source=None, confidence="D",
    why="The first trade after years with nobody bidding is one buyer's price in a market that had no "
        "buyers, and the market's usual volume has run down to nothing, so the volume rule would adopt "
        "it whole. Buyers and sellers who watched the market go quiet weigh it against the price it "
        "had drifted to. Unmeasured.")


REPRESENTATIVE_TRADE_SHARE = declare(
    "REPRESENTATIVE_TRADE_SHARE", 0.25, kind="temporary_heuristic",
    unit="share of what buyers wanted at the remembered price that a trade must reach to count in full",
    source=None, confidence="D",
    why="A trade of a few units in a market where buyers want far more is priced by those few units' "
        "scarcity, not by what buyers pay for the volume they want, and a market that has only ever "
        "traded slivers has a usual volume that is itself a sliver. Against the usual volume alone the "
        "memory would adopt such a price whole. How small a trade must be to say little has no measured "
        "basis.")


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


def memory_reference_volume(usual_volume: float, wanted_at_old_price: float) -> float:
    """The volume a trade is weighed against: the market's usual volume, or when that is a sliver next
    to what buyers wanted at the remembered price, a share of what they wanted."""
    return max(usual_volume, REPRESENTATIVE_TRADE_SHARE * wanted_at_old_price)


def price_after_resumed_trade(old: Optional[float], volume_rule_price: float, years_without_bids: int) -> float:
    """After trade resumes, the remembered price moves only part of the way from the price the quiet
    market drifted to."""
    if old is None or years_without_bids <= 0:
        return volume_rule_price
    return old + RESUMED_TRADE_MEMORY_SHARE * (volume_rule_price - old)


def wanted_at(bids: Sequence[Bid], price: Optional[float]) -> float:
    """What the market's own buyers would have taken at a price (budgets and ceilings applied); zero
    without a price. A foreign partner's order is sized by the partner, not by what the market usually
    trades, so it does not count: left in, it makes any home trade a sliver and freezes the memory."""
    if not price or price <= 0.0:
        return 0.0
    return math.fsum([quantity_at(bid, price) for bid in bids if bid.buyer != EDGE_EXTERNAL])
