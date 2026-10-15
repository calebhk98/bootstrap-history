"""This year's revenue of an output-derived node against its long-run figure.

The node's baskets are valued at solved long-run prices (the cost of making) when the tree loads.
In a given year what it sells and what it buys each trade at the price the economy shows on the founder's
tile; the factor is the year's net over the long-run net.
"""
from typing import Callable, Mapping, Optional


def market_factor(node: Mapping, long_run_prices: Mapping[str, float],
                  price_now: Callable[[str], Optional[float]]) -> float:
    """Net sales this year over net sales at long-run cost; one for a node with no baskets. A material
    nothing prices now is valued at its long-run cost."""
    sold = node.get("_output_per_year")
    if not sold:
        return 1.0
    bought = node.get("_purchases_per_year") or {}
    long_run = this_year = 0.0
    for basket, sign in ((sold, 1.0), (bought, -1.0)):
        for material, quantity in basket.items():
            cost = long_run_prices.get(material, 0.0)
            if cost <= 0.0:
                continue
            paid = price_now(material)
            long_run += sign * quantity * cost
            this_year += sign * quantity * (cost if paid is None else paid)
    if long_run <= 0.0:
        return 1.0
    return max(0.0, this_year) / long_run
