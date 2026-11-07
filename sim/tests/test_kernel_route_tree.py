"""The kernel `routes_tree_kernel.least_tree` called on random graphs against the plain heap search it replaced."""

QUICK_TOPIC = True

import heapq
import random
import unittest

import numpy as np

from sim.geography.routes_tree_kernel import INFINITY, least_tree


def random_graph(generator, states, edges_per_state):
    """Compressed rows for a random graph; costs and days come from a few values so ties are common."""
    first, target, cost, days = [0], [], [], []
    for _state in range(states):
        for _edge in range(generator.randint(0, edges_per_state)):
            target.append(generator.randrange(states))
            cost.append(generator.choice([0.5, 1.0, 1.5, 2.0, 3.25]))
            days.append(generator.choice([0.25, 0.5, 1.0, 2.0]))
        first.append(len(target))
    return first, target, cost, days


def plain_tree(first, target, cost_of, days_of, starts, by_days):
    """The heap search over (priority, state) pairs: (cost, days, edge into each state or -1)."""
    size = len(first) - 1
    cost, days, into = [INFINITY] * size, [INFINITY] * size, [-1] * size
    queue = []
    for state, start_cost, start_days in starts:
        cost[state], days[state] = start_cost, start_days
        heapq.heappush(queue, (start_days if by_days else start_cost, state))
    settled = [False] * size
    while queue:
        _priority, state = heapq.heappop(queue)
        if settled[state]:
            continue
        settled[state] = True
        for edge in range(first[state], first[state + 1]):
            to_state = target[edge]
            if settled[to_state]:
                continue
            new_cost, new_days = cost[state] + cost_of[edge], days[state] + days_of[edge]
            if new_days < days[to_state] if by_days else new_cost < cost[to_state]:
                cost[to_state], days[to_state], into[to_state] = new_cost, new_days, edge
                heapq.heappush(queue, (new_days if by_days else new_cost, to_state))
    return cost, days, into


def kernel_tree(first, target, cost_of, days_of, starts, by_days):
    return least_tree(np.array(first, dtype=np.int64), np.array(target, dtype=np.int64),
                      np.array(cost_of, dtype=np.float64), np.array(days_of, dtype=np.float64),
                      np.array([start[0] for start in starts], dtype=np.int64),
                      np.array([start[1] for start in starts], dtype=np.float64),
                      np.array([start[2] for start in starts], dtype=np.float64), by_days)


class LeastTreeKernelTest(unittest.TestCase):
    def test_costs_days_and_edges_match_the_plain_search_by_cost_and_by_days(self):
        generator = random.Random(7)
        for case in range(60):
            states = generator.randint(1, 40)
            first, target, cost_of, days_of = random_graph(generator, states, 4)
            starts = [(generator.randrange(states), generator.choice([0.0, 0.5]), generator.choice([0.0, 0.25]))
                      for _start in range(generator.randint(1, 3))]
            starts = list({start[0]: start for start in starts}.values())
            for by_days in (False, True):
                expected = plain_tree(first, target, cost_of, days_of, starts, by_days)
                found = kernel_tree(first, target, cost_of, days_of, starts, by_days)
                for want, got in zip(expected, found):
                    self.assertEqual(want, got.tolist(), msg="case %d by_days %s" % (case, by_days))

    def test_a_state_with_no_edges_and_no_starts_reached_stays_unreached(self):
        cost, days, into = kernel_tree([0, 0, 0], [], [], [], [(0, 0.0, 0.0)], False)
        self.assertEqual([0.0, INFINITY], cost.tolist())
        self.assertEqual([0.0, INFINITY], days.tolist())
        self.assertEqual([-1, -1], into.tolist())

    def test_no_states_gives_empty_arrays(self):
        cost, days, into = kernel_tree([0], [], [], [], [], False)
        self.assertEqual(0, len(cost) + len(days) + len(into))


if __name__ == "__main__":
    unittest.main()
