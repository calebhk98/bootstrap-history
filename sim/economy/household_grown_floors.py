"""The share of each floor the household's own plot grew: that share is met before the year's budget is sized."""
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
