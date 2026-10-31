"""How far a quote, as against a price a market settled at, may pull a producer's expectation."""
from typing import Mapping, Optional

from . import ask_adjust
from .market_memory import PRICE_TRADED
from .types import QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK

# A best unfilled bid is one buyer's ceiling (the largest maximum among the bids, not a price anyone paid) and a lowest
# unfilled ask is a seller's own ask coming back to it. Either is the only signal a market with no trade gives a maker,
# so it is read, but only as far as the band around the unit's cost (`ask_adjust.band_edge`): a ceiling far above cost
# says buyers want the good, not what it will fetch.
BARE_QUOTES = (QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK)


def is_bare_quote(view, good, area) -> bool:
    """True when the market's price for `good` in `area` is a bid ceiling or an ask, not a price that traded. A view
    that does not say what its prices are (`price_kind`) is taken to give prices."""
    kind_of = getattr(view, "price_kind", None)
    return kind_of is not None and kind_of(good, area) in BARE_QUOTES


def held_to_band(expected: float, previous: Optional[float], unit_cost: Optional[float], input_share: float) -> float:
    """`expected`, drawn from a bare quote, kept no higher than the band edge around `unit_cost` or the `previous`
    expectation, whichever is higher (a quote never cuts an expectation here, and never lifts it past the band).
    Unchanged when no unit cost can be worked out."""
    if unit_cost is None or not unit_cost > 0.0:
        return expected
    ceiling = ask_adjust.band_edge(unit_cost, input_share)
    if previous is not None:
        ceiling = max(ceiling, previous)
    return min(expected, ceiling)
