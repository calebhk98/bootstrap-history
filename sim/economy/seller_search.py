"""Pruned search over a seller's candidate reservations.

For a seller whose only offer in the market is the one being priced, raising its reservation never raises
what it sells and never lowers the clearing price. So between two reservations already tried, no reservation
can earn more than the dearer one's price less the unit value, times the cheaper one's sales. A stretch of
candidates whose bound cannot beat the best profit found is skipped without clearing the market for them.
"""
import heapq
from typing import Callable, List, Tuple

from .accounts import ROUNDING_SHARE


def _bound(price_high: float, sold_low: float, sold_high: float, unit_value: float) -> float:
    margin = price_high - unit_value
    return margin * (sold_low if margin >= 0.0 else sold_high)


def evaluated_points(points: List[float], tried_first: List[float],
                     outcome_at: Callable[[float], Tuple[float, float]], unit_value: float) -> List[float]:
    """The reservations among `points` (ascending) worth clearing: those in `tried_first`, then each stretch
    between tried reservations whose bound could still beat the best profit seen. `outcome_at(reservation)`
    gives (what the seller sells, clearing price)."""
    index_of = {point: index for index, point in enumerate(points)}
    tried = {}

    def try_index(index: int) -> float:
        if index not in tried:
            sold, price = outcome_at(points[index])
            tried[index] = (sold, price, (price - unit_value) * sold)
        return tried[index][2]

    best = None
    for point in tried_first:
        profit = try_index(index_of[point])
        best = profit if best is None else max(best, profit)
    heap: list = []

    def push(low: int, high: int) -> None:
        if high - low <= 1:
            return
        sold_low, _, _ = tried[low]
        sold_high, price_high, _ = tried[high]
        heapq.heappush(heap, (-_bound(price_high, sold_low, sold_high, unit_value), low, high))

    ordered = sorted(tried)
    for low, high in zip(ordered, ordered[1:]):
        push(low, high)
    while heap:
        negative_bound, low, high = heapq.heappop(heap)
        if -negative_bound <= best + ROUNDING_SHARE * max(abs(best), 1e-300):
            break
        middle = (low + high) // 2
        best = max(best, try_index(middle))
        push(low, middle)
        push(middle, high)
    return [points[index] for index in sorted(tried)]
