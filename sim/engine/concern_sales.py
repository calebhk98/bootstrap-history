"""What a seat's concern output fetches when the year's goods market clears it, and what a forecast may assume of it.

A seat's concerns offer their year's output into the one goods clearing at a seller's ask (the same offers a firm's
plant makes). The money the clearing pays is for the units buyers took at the cleared price; the rest is returned
unsold. These rules turn the clearing's result into a per-material record and the record into the share of an
output the next forecast may count as sold.
"""
from typing import Dict, Mapping, NamedTuple, Optional

CLEARED_LAST_YEAR = "cleared_last_year"
BUYERS_LAST_YEAR = "buyers_last_year"
NO_MARKET_YET = "no_market_yet"


class SaleResult(NamedTuple):
    """One material a seat offered into a year's clearing: units offered, units buyers took, money received."""
    offered: float
    sold: float
    proceeds: float


class Outlook(NamedTuple):
    """What a forecast may assume of a seat's output of one material: the share that sells, the money a unit that
    sold fetched (None when none sold, so the caller keeps the ask), and what the share stands on."""
    share: float
    price: Optional[float]
    basis: str


def settle_sales(offered: Mapping[str, float], unsold: Mapping[str, float], proceeds: float,
                 price_of: Mapping[str, float]) -> Dict[str, SaleResult]:
    """Per-material result of a clearing: `offered` units per material, `unsold` units returned, and the `proceeds`
    the account holds, shared among the materials by units sold at `price_of` (units priced alike when a material
    has no price). A material whose units all came back receives nothing."""
    sold = {material: max(0.0, units - unsold.get(material, 0.0)) for material, units in offered.items()}
    weights = {material: units * (price_of.get(material) or 1.0) for material, units in sold.items()}
    total = sum(weights.values())
    return {material: SaleResult(offered[material], sold[material],
                                 proceeds * weights[material] / total if total > 0.0 else 0.0)
            for material in sorted(offered)}


def outlook(result: Optional[SaleResult], buyers_units: Optional[float], quantity: float) -> Optional[Outlook]:
    """The share of `quantity` units a forecast may count as sold: what the seat's own last clearing sold of what it
    offered; else what the market's buyers took and still wanted last year (`buyers_units`, sold plus unmet) as a
    share of the quantity; None when neither is known."""
    if result is not None and result.offered > 0.0:
        return Outlook(min(1.0, result.sold / result.offered),
                       result.proceeds / result.sold if result.sold > 0.0 else None, CLEARED_LAST_YEAR)
    if buyers_units is not None and quantity > 0.0:
        return Outlook(min(1.0, max(0.0, buyers_units) / quantity), None, BUYERS_LAST_YEAR)
    return None
