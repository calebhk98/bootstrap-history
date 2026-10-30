"""Sharing a limited quantity among buyers' wants: lower priority tiers are served first, a tier that cannot be served
in full shares what is left pro rata (Eurace@Unibi, Cons_Goods/Mall_functions.c, Mall_update_mall_stocks_sales_rationing_1:
rationing_rate = stock / aggregated_demand, there across all requests since Eurace has no tiers)."""
import math
from itertools import groupby
from operator import attrgetter
from typing import List, Sequence

from .types import Bid

_PRIORITY = attrgetter("priority")


def ration(bids: Sequence[Bid], wants: List[float], available: float) -> List[float]:
    """Serve each priority tier in turn; a tier that cannot be served in full shares what is left pro rata."""
    result: List[float] = []
    remaining = available
    start = 0
    for _tier, tier_group in groupby(bids, key=_PRIORITY):
        end = start + sum(1 for _ in tier_group)
        tier_wants = wants[start:end]
        start = end
        total = math.fsum(tier_wants)
        if total <= 0.0:
            result.extend([0.0] * len(tier_wants))
        elif remaining >= total:
            result.extend(tier_wants)
            remaining -= total
        else:
            share = remaining / total
            result.extend([want * share for want in tier_wants])
            remaining = 0.0
    return result
