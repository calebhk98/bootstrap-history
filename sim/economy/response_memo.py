"""A market's price response, kept while its book stands.

`market_curves.price_response` clears a market's summarised book again with one more order and is a function of the book's
content, the good, the last price and the order alone. A year asks the same question of the same book many times (the
state's costing, the household's holdings, a purchase quote read at a few slices each), so the answer is kept against the
book it was worked out from: an entry is served only while the book object it was made from is the one asked about. A
book is written once a year as a new object (`year_goods`) and never changed in place, so a new clearing, a load or a
rebuilt book finds no entry and works the answer out afresh. The memory is emptied when it grows large."""
from typing import Dict, List, Optional, Tuple

from . import market_curves

RESPONSES_KEPT = 8192
_RESPONSES: Dict[tuple, Tuple[object, Optional[float]]] = {}


def price_response(curve: Dict[str, List[List[float]]], good: str, last_price: Optional[float], landed: float,
                   taken: float) -> Optional[float]:
    """`market_curves.price_response` of the same arguments, kept against `curve` (the book object): the factor on the
    price once `landed` more are offered and `taken` more are bought, None when the book traded nothing."""
    key = (id(curve), good, last_price, landed, taken)
    found = _RESPONSES.get(key)
    if found is not None and found[0] is curve:
        return found[1]
    factor = market_curves.price_response(curve, good, last_price, landed, taken)
    if len(_RESPONSES) >= RESPONSES_KEPT:
        _RESPONSES.clear()
    _RESPONSES[key] = (curve, factor)   # holding the book keeps its id from being taken by another object
    return factor
