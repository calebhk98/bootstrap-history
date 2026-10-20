"""A registered town provider sets the size of a tile's town, bounded by the tile's people; None means no opinion.

Builds a whole game, so it is not in the quick tier."""
import os
import random
import sys
import unittest

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, _REPOSITORY_ROOT)
from sim import simulator
from sim.engine import mod_code
from sim.engine.core import Sim
from sim.labour import town_providers
from sim.tests.harness import build_unopened

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()
NAME = "test_acme_k3f9:towns"


class TownProviderTests(unittest.TestCase):
    def setUp(self):
        self.sim = build_unopened(lambda: Sim(_NODES, list(_NODES), random.Random(1), civ=simulator.load_civ("rome_100ad")))
        self.addCleanup(town_providers.PROVIDERS.clear)

    def test_no_provider_leaves_the_nominal_town(self):
        tile = self.sim.labour.base_tile()
        self.assertEqual(self.sim.labour.home_town_population_estimate(), self.sim.labour._town_population_at(tile))

    def test_provider_sets_the_town_and_none_declines(self):
        tile = self.sim.labour.base_tile()
        nominal = self.sim.labour.home_town_population_estimate()
        mod_code.ModCodeApi("test_acme_k3f9").town_provider("towns", lambda labour, where, size: 0.5 * size)
        self.assertEqual(self.sim.labour.home_town_population_estimate(), 0.5 * nominal)
        town_providers.PROVIDERS["test_acme_k3f9:zz_silent"] = lambda labour, where, size: None
        self.assertEqual(self.sim.labour.home_town_population_estimate(), 0.5 * nominal)
        self.assertIn(tile, self.sim.labour.settlement_tiles())

    def test_provided_town_never_exceeds_the_tile_people(self):
        tile = self.sim.labour.base_tile()
        people = self.sim.labour.settlement_tiles()[tile]
        town_providers.register_town_provider(NAME, lambda labour, where, size: people * 10.0)
        self.assertEqual(self.sim.labour.home_town_population_estimate(), people)


if __name__ == "__main__":
    unittest.main()
