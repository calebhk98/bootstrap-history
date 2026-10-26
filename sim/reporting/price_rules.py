"""Price ratios in real terms, on plain values: a good's price set against the other goods' prices, both in the agent
economy's own coin, so no money scale enters.

A price over the incumbents' cost is a ratio across scales: the cost follows the money per labour hour, which follows
the coin's revaluation, so a revaluation measured that way moves itself (a loop). Here a good's price is set against
a basket fixed at the baseline (the first close that read it), which the money per labour hour does not drive."""
import math
from typing import Dict, Optional, Set


def opening_baseline(prices: Dict[str, float]) -> Dict[str, float]:
    """The baseline a first read fixes: every good priced above nothing."""
    return {good: price for good, price in prices.items() if price > 0.0}


def basket_level(prices: Dict[str, float], baseline: Dict[str, float], excluded: Set[str]) -> float:
    """The geometric mean of the basket's price change against the baseline, leaving the excluded goods out; one when
    nothing is left."""
    logs = [math.log(prices[good] / base) for good, base in sorted(baseline.items())
            if good not in excluded and prices.get(good, 0.0) > 0.0]
    return math.exp(sum(logs) / len(logs)) if logs else 1.0


def price_ratio(base: Optional[float], now: Optional[float], level: float) -> float:
    """The good's price now over its baseline, over the basket's change; one where either price is missing."""
    if not base or not now or now <= 0.0:
        return 1.0
    return (now / base) / level


def wage_ratio(ratio: Optional[float]) -> float:
    """A ratio a wage may read: one where there is none or it is not above nothing."""
    return ratio if ratio and ratio > 0.0 else 1.0
