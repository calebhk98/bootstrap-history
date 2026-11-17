"""The share of each floor the household's own plot grew: that share is met before the year's budget is sized."""
import math
from typing import Dict, Mapping, Tuple


def met_shares(basket, people: float, grown_units: Mapping[str, float]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """(share of each need's floor the plot grew, by need id; the same share by good, taken from the first need naming the good)."""
    by_need: Dict[str, float] = {}
    by_good: Dict[str, float] = {}
    for need in basket.needs:
        floor_units = need.subsistence_per_person * people
        met = min(1.0, grown_units.get(need.need_id, 0.0) / floor_units) if floor_units > 0.0 else 0.0
        by_need[need.need_id] = met
        for good, _effect in need.goods:
            by_good.setdefault(good, met)
    return by_need, by_good


def floor_cost_met(priced, people: float, met_by_need: Mapping[str, float]) -> float:
    """What the floors the plot grew would have cost at the needs' price indexes: the spending the household makes in kind."""
    return math.fsum(need.price_index * need.spec.subsistence_per_person * people * met_by_need.get(need.spec.need_id, 0.0)
                     for need in priced)
