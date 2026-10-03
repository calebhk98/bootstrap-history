"""What one household of a cohort can pay for one unit of a good.

A cohort stands for many households of one income class. A household cannot pay more for a unit of a
good than it spends on the need that good serves, so the cohort's bid for that good stops at that price
however large the cohort's total budget is. Goods a household cannot afford get no bid; the need's
spending moves to the goods it can.
"""
import math
from typing import Dict, Sequence, Tuple

from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD


def household_budget_for_need(need_units: float, price_index: float, people: float) -> float:
    """Money one household plans to spend on a need in the year: its share of the cohort's need units
    at the need's price index."""
    if people <= 0.0:
        return 0.0
    return need_units * price_index * PERSONS_PER_HOUSEHOLD / people


def affordable_goods(goods: Sequence[Tuple[str, float, float, float]],
                     household_budget: float, has_floor: bool) -> Tuple[Dict[str, bool], float, float]:
    """Which goods of a need one household can pay for one unit of, and the share of the need's
    spending they carry (to scale up so the spending is all placed), and the price cap to put on a bid
    (infinite if no good is affordable and the need has a floor: every good then stays uncapped, so that
    a need's floor is never dropped; a need without a floor is not bought at all that year)."""
    affordable = {good: price <= household_budget for good, price, _effect, _share in goods}
    share = math.fsum(row[3] for row in goods if affordable[row[0]])
    if share <= 0.0:
        if not has_floor:
            return affordable, 1.0, household_budget
        return {good: True for good in affordable}, 1.0, math.inf
    return affordable, share, household_budget
