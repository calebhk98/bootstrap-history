"""The least that moving a person costs from one area to every area a way leads to: the one search the import cap and the
bonded market share. Plain function."""
import heapq
import math
from typing import Dict, List, Mapping, Sequence, Tuple


def carriage_from(routes: Mapping[str, Sequence], origin: str) -> Dict[str, float]:
    """The cheapest total `moving_cost` along the routes (`Route`-like rows with `destination` and `moving_cost`) from `origin`
    to every area a way leads to; the origin costs 0. A route never pays you to move: a negative or unknown cost counts as 0."""
    best: Dict[str, float] = {origin: 0.0}
    queue: List[Tuple[float, str]] = [(0.0, origin)]
    while queue:
        cost, area = heapq.heappop(queue)
        if cost > best.get(area, math.inf):
            continue
        for route in routes.get(area, ()):
            step = cost + max(0.0, route.moving_cost)
            if step < best.get(route.destination, math.inf):
                best[route.destination] = step
                heapq.heappush(queue, (step, route.destination))
    return best
