"""What a buyer reads of a market: the offers on it, not a remembered price (Complaint 642).

Eurace's consumers see the mall's current prices and nothing else (Cons_Goods/Household_Consumer_Functions.c); a buyer
here sees the price a market traded at or an ask still posted, and None where nothing is on offer.
"""
from typing import Optional

from .types import AreaId, GoodId


def offered_price(view, good: GoodId, area: AreaId) -> Optional[float]:
    """`view.offered_price(good, area)`; a view that does not separate offers from remembered prices gives its `price`."""
    own = getattr(view, "offered_price", None)
    return own(good, area) if own is not None else view.price(good, area)
