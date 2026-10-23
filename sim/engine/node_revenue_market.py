"""This year's revenue of an output-derived node against its long-run figure.

The node's baskets are valued at solved long-run prices (the cost of making) when the tree loads.
In a given year what it sells and what it buys each trade at the price the economy shows on the founder's
tile; the factor is the year's net over the long-run net.
"""
from typing import Callable, Mapping, Optional

from .concern_sales import Outlook


def basket_market_factor(sold: Mapping[str, float], bought: Mapping[str, float],
                         long_run_prices: Mapping[str, float],
                         price_now: Callable[[str], Optional[float]],
                         sale_outlook: Optional[Callable[[str, float], Optional[Outlook]]] = None) -> float:
    """Net sales this year over net sales at long-run cost, for what an entry sells and buys in a year; one
    where nothing is sold. A material nothing prices now is valued at its long-run cost. `sale_outlook(material,
    quantity)` says what share of the quantity buyers take and at what price; only that share of a sold basket
    counts, at that price when one sold (else at `price_now`)."""
    if not sold:
        return 1.0
    long_run = this_year = 0.0
    for basket, sign in ((sold, 1.0), (bought, -1.0)):
        for material, quantity in basket.items():
            cost = long_run_prices.get(material, 0.0)
            if cost <= 0.0:
                continue
            paid = price_now(material)
            share = 1.0
            if sign > 0.0 and sale_outlook is not None:
                taken = sale_outlook(material, quantity)
                if taken is not None:
                    share = taken.share
                    paid = taken.price if taken.price is not None else paid
            long_run += sign * quantity * cost
            this_year += sign * quantity * share * (cost if paid is None else paid)
    if long_run <= 0.0:
        return 1.0
    return max(0.0, this_year) / long_run


def market_factor(node: Mapping, long_run_prices: Mapping[str, float],
                  price_now: Callable[[str], Optional[float]]) -> float:
    """`basket_market_factor` for an output-derived node's yearly baskets; one for a node with none."""
    return basket_market_factor(node.get("_output_per_year") or {}, node.get("_purchases_per_year") or {},
                                long_run_prices, price_now)
