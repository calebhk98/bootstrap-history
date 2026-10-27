"""The kernel `markets.least_cost_tree` (sim/geography/routes_cost_tree.py) called on its own samples against a plain relaxation."""

QUICK_TOPIC = True

import unittest

from sim.geography.routes_cost_tree import INFINITY, least_cost_tree, settled_costs
from sim.geography.routes_cost_tree_samples import MODES, samples
from sim.markets.kernels import KERNELS, LEAST_COST_TREE


def relaxed(adjacency, starts):
    """Least cost by relaxing every link until none improves: no queue, so no search order to get wrong."""
    cost = [INFINITY] * len(adjacency)
    for start_cost, state in starts:
        cost[state] = min(cost[state], start_cost)
    changed = True
    while changed:
        changed = False
        for state, steps in enumerate(adjacency):
            for to_state, step_cost in steps:
                if cost[state] + step_cost < cost[to_state]:
                    cost[to_state] = cost[state] + step_cost
                    changed = True
    return cost


class LeastCostTreeKernelTest(unittest.TestCase):
    def test_a_full_search_gives_the_least_cost_of_every_state(self):
        for (adjacency, starts, per_tile, settle), keywords in samples():
            if not settle:
                found = least_cost_tree(adjacency, starts, per_tile, settle, **keywords)
                for state, (expected, got) in enumerate(zip(relaxed(adjacency, starts), found)):
                    self.assertAlmostEqual(expected, got, places=9, msg="state %d" % state)

    def test_a_search_stopped_at_some_tiles_has_their_least_cost_final(self):
        stopped = 0
        for (adjacency, starts, per_tile, settle), keywords in samples():
            if settle:
                stopped += 1
                found = least_cost_tree(adjacency, starts, per_tile, settle, **keywords)
                full = relaxed(adjacency, starts)
                for tile in settle:
                    states = range(tile * per_tile, (tile + 1) * per_tile)
                    self.assertAlmostEqual(min(full[state] for state in states), min(found[state] for state in states), places=9)
        self.assertGreaterEqual(stopped, 2)

    def test_an_empty_set_of_tiles_to_settle_searches_everything(self):
        adjacency, starts, per_tile, _settle = samples()[0][0]
        self.assertEqual(least_cost_tree(adjacency, starts, per_tile, set()), least_cost_tree(adjacency, starts, per_tile, None))

    def test_the_start_states_cost_what_they_are_started_at(self):
        found = least_cost_tree([[(1, 1.0)], []], [(0.5, 0)], 1)
        self.assertEqual(found, [0.5, 1.5])

    def test_an_unreachable_state_stays_infinite(self):
        self.assertEqual(least_cost_tree([[], []], [(0.0, 0)], 1), [0.0, INFINITY])

    def test_what_is_contractual_is_the_least_over_each_settled_tile(self):
        costs = [5.0, 3.0, 4.0, 9.0, 2.0, 8.0]
        self.assertEqual(settled_costs(([], [], 3, {1, 0}), {}, costs), [3.0, 2.0])
        self.assertEqual(settled_costs(([], [], 3, None), {}, costs), costs)
        self.assertEqual(settled_costs(([], [], 3, set()), {}, costs), costs)

    def test_the_kernel_is_declared_with_these_samples(self):
        kernel = next(each for each in KERNELS if each.name == LEAST_COST_TREE)
        self.assertIs(kernel.reference, least_cost_tree)
        self.assertEqual(len(kernel.samples()), len(samples()))
        self.assertEqual(MODES, 3)


if __name__ == "__main__":
    unittest.main()
