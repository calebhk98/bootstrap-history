"""The least that moving a person costs from one area to every area a way leads to: the one search the import cap and the
bonded market share. Plain function, and the same search from every origin at once over arrays (`carriage_table`)."""
import heapq
import math
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np

from sim.jit import njit


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


@njit
def all_cheapest(cost):
    """The cheapest total cost between every pair of areas from the matrix of single-way costs (infinity where there is no way,
    zero on the diagonal), by relaxing through each area in turn; rows with no way out of them are skipped."""
    count = cost.shape[0]
    for through in range(count):
        for source in range(count):
            first = cost[source, through]
            if first == np.inf:
                continue
            for destination in range(count):
                step = first + cost[through, destination]
                if step < cost[source, destination]:
                    cost[source, destination] = step
    return cost


def carriage_table(routes: Mapping[str, Sequence]) -> Dict[str, Dict[str, float]]:
    """`carriage_from` for every area the routes start from, in one search: {origin: {area: cheapest cost}}, each origin
    reaching itself at 0. Sums along a path may differ from `carriage_from`'s in the last digit (added in another order)."""
    names = sorted(set(routes) | {route.destination for each in routes.values() for route in each})
    position = {name: index for index, name in enumerate(names)}
    cost = np.full((len(names), len(names)), np.inf)
    for index in range(len(names)):
        cost[index, index] = 0.0
    for origin, ways in routes.items():
        row = position[origin]
        for route in ways:
            column = position[route.destination]
            step = max(0.0, route.moving_cost)
            if step < cost[row, column]:
                cost[row, column] = step
    cost = all_cheapest(cost)
    table: Dict[str, Dict[str, float]] = {}
    for name in names:
        row = cost[position[name]]
        reached = np.flatnonzero(row < np.inf).tolist()
        table[name] = {names[column]: value for column, value in zip(reached, row[reached].tolist())}
    return table
