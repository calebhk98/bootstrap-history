"""This year's revenue of an output-derived node against its long-run figure.

The node's baskets are valued at solved long-run prices when the tree loads.
In a given year what it sells and what it buys each trade at the market's price
over that cost (`Sim.market_price_ratio`); the factor is the year's net over the
long-run net.
"""
from typing import Callable, Mapping, Optional


def market_factor(node: Mapping, goods: Mapping[str, float],
                  ratio_of: Callable[[str], Optional[float]]) -> float:
    """Net sales this year over net sales at long-run cost; one for a node with no baskets."""
    sold = node.get("_output_per_year")
    if not sold:
        return 1.0
    bought = node.get("_purchases_per_year") or {}
    long_run = this_year = 0.0
    for basket, sign in ((sold, 1.0), (bought, -1.0)):
        for material, quantity in basket.items():
            value = quantity * goods.get(material, 0.0)
            long_run += sign * value
            this_year += sign * value * (ratio_of(material) or 1.0)
    if long_run <= 0.0:
        return 1.0
    return max(0.0, this_year) / long_run
