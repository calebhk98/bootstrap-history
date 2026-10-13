"""The cost-only search behind `route_costs` finds the costs the full search finds, whole or stopped early."""
import random
import unittest

from sim.geography import queries, routes_compile, routes_modes, routes_search

QUICK_TOPIC = False


class RouteCostsSearchTests(unittest.TestCase):
    def setUp(self):
        self.world_map = queries._map(None)
        self.tiles = sorted(self.world_map.tiles)
        self.mode_ids = list(routes_modes.modes(self.world_map))
        self.rates = {mode: 1.0 + 0.37 * index for index, mode in enumerate(self.mode_ids)}
        self.handling = {mode: 0.3 * index for index, mode in enumerate(self.mode_ids)}
        self.compiled = routes_compile.compiled_for(self.world_map, self.mode_ids, {}, self.rates, self.handling, [])

    def test_cost_search_matches_the_full_search(self):
        for origin in random.Random(1).sample(self.tiles, 8):
            full = routes_search._tree(self.compiled, frozenset([origin]), False)[0]
            self.assertEqual(routes_search._cost_tree(self.compiled, frozenset([origin])), full)

    def test_stopping_early_leaves_the_asked_tiles_unchanged(self):
        chosen = random.Random(2).sample(self.tiles, 40)
        for origin in chosen[:5]:
            whole = routes_search.costs_from(self.world_map, [origin], self.mode_ids, {}, self.rates, self.handling, [])
            early = routes_search.costs_from(self.world_map, [origin], self.mode_ids, {}, self.rates, self.handling, [],
                                             within=chosen)
            self.assertEqual(early, {tile: cost for tile, cost in whole.items() if tile in set(chosen)})
            self.assertEqual(list(early), [tile for tile in whole if tile in set(chosen)])


if __name__ == "__main__":
    unittest.main()
