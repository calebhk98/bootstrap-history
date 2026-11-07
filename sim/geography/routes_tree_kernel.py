"""The kernel behind `routes_search._tree`: the least-cost or fastest tree from some start states over the (tile, mode)
graph packed into arrays (compressed rows: the edges of state `s` are `first_edge[s]` up to `first_edge[s + 1]`).

The queue orders (priority, state) pairs and a state settles once, so the answer does not depend on the queue's layout;
edges are relaxed in array order and sums run from the start, so costs and days are those of the plain search."""
import numpy as np

from sim.jit import njit

INFINITY = float("inf")


@njit
def _push(priorities, states, size, priority, state):
    position = size
    while position > 0:
        parent = (position - 1) // 2
        if priorities[parent] < priority or (priorities[parent] == priority and states[parent] <= state):
            break
        priorities[position] = priorities[parent]
        states[position] = states[parent]
        position = parent
    priorities[position] = priority
    states[position] = state


@njit
def _pop_into(priorities, states, size):
    """Remove the smallest pair of a queue holding `size` pairs; the caller has read pair 0 already."""
    last_priority = priorities[size - 1]
    last_state = states[size - 1]
    remaining = size - 1
    position = 0
    while True:
        child = 2 * position + 1
        if child >= remaining:
            break
        other = child + 1
        if other < remaining and (priorities[other] < priorities[child]
                                  or (priorities[other] == priorities[child] and states[other] < states[child])):
            child = other
        if last_priority < priorities[child] or (last_priority == priorities[child] and last_state <= states[child]):
            break
        priorities[position] = priorities[child]
        states[position] = states[child]
        position = child
    if remaining > 0:
        priorities[position] = last_priority
        states[position] = last_state


@njit
def least_tree(first_edge, edge_to, edge_cost, edge_days, start_states, start_costs, start_days, by_days):
    """(cost, days, edge into each state or -1) from the start states, searching by days when `by_days` else by cost."""
    size = len(first_edge) - 1
    cost = np.full(size, INFINITY)
    days = np.full(size, INFINITY)
    previous = np.full(size, -1, dtype=np.int64)
    settled = np.zeros(size, dtype=np.bool_)
    capacity = len(edge_to) + len(start_states) + 1
    priorities = np.empty(capacity)
    states = np.empty(capacity, dtype=np.int64)
    queued = 0
    for index in range(len(start_states)):
        state = start_states[index]
        cost[state] = start_costs[index]
        days[state] = start_days[index]
        _push(priorities, states, queued, start_days[index] if by_days else start_costs[index], state)
        queued += 1
    while queued > 0:
        state = states[0]
        _pop_into(priorities, states, queued)
        queued -= 1
        if settled[state]:
            continue
        settled[state] = True
        here_cost = cost[state]
        here_days = days[state]
        for edge in range(first_edge[state], first_edge[state + 1]):
            to_state = edge_to[edge]
            if settled[to_state]:
                continue
            new_cost = here_cost + edge_cost[edge]
            new_days = here_days + edge_days[edge]
            if (new_days < days[to_state]) if by_days else (new_cost < cost[to_state]):
                cost[to_state] = new_cost
                days[to_state] = new_days
                previous[to_state] = edge
                _push(priorities, states, queued, new_days if by_days else new_cost, to_state)
                queued += 1
    return cost, days, previous
