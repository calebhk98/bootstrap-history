"""The kernel behind `routes_search._cost_tree`: least cost to every state of the (tile, mode) graph from some start states.

A plain function of plain inputs, so a mod can swap in a faster one (Complaint 661)."""
import heapq
from typing import Collection, List, Optional, Sequence, Tuple

INFINITY = float("inf")

Adjacency = Sequence[Sequence[Tuple[int, float]]]      # per state, (state reached, cost added)


def least_cost_tree(adjacency: Adjacency, starts: Sequence[Tuple[float, int]], states_per_tile: int,
                    settle_tiles: Optional[Collection[int]] = None) -> List[float]:
    """The least cost to every state, a path's cost summed in order from its start whatever the search order.

    `adjacency[state]` lists (state reached, cost added); a tile's states are `tile * states_per_tile + mode`. `starts`
    are (cost, state) of the states the search begins from. With `settle_tiles` (tile indexes, not empty) the search
    stops once each of those tiles has had a state settled: the least cost over a listed tile's states is final, other
    entries are not."""
    cost = [INFINITY] * len(adjacency)
    queue = []
    for start_cost, state in starts:
        cost[state] = start_cost
        queue.append((start_cost, state))
    heapq.heapify(queue)
    pop, push = heapq.heappop, heapq.heappush
    unsettled = None if settle_tiles is None else set(settle_tiles)
    while queue:
        here_cost, state = pop(queue)
        if here_cost > cost[state]:
            continue
        if unsettled:
            unsettled.discard(state // states_per_tile)
            if not unsettled:
                break
        for to_state, step_cost in adjacency[state]:
            new_cost = here_cost + step_cost
            if new_cost < cost[to_state]:
                cost[to_state] = new_cost
                push(queue, (new_cost, to_state))
    return cost


def settled_costs(arguments: tuple, keywords: dict, cost: List[float]):
    """The part of an answer that is contractual: all of it, or the least cost over each listed tile's states."""
    adjacency, starts, states_per_tile = arguments[:3]
    settle_tiles = arguments[3] if len(arguments) > 3 else keywords.get("settle_tiles")
    if not settle_tiles:
        return cost
    return [min(cost[tile * states_per_tile:(tile + 1) * states_per_tile]) for tile in sorted(settle_tiles)]
