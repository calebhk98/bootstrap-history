"""SCENARIO (backing margin cache): on a game's own setup the kept backing-good margin is what a fresh opening of its
economy gives, and asking again returns the kept one. The cache rules on built setups are in test_backing_margin_cache."""
import tempfile
import unittest
from unittest import mock

from sim.economy import api as economy_api
from sim.engine import economy_port_coin
from sim.engine.economy_port_setup import build_setup, opening_values

from .harness import unopened_sim


class BackingMarginCacheScenarioTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="backing_margin_")
        patch = mock.patch.object(economy_port_coin, "MARGIN_CACHE_DIRECTORY", self.directory)
        patch.start()
        self.addCleanup(patch.stop)

    def test_the_kept_margin_is_what_a_fresh_opening_gives(self):
        game = unopened_sim()
        setup = build_setup(game, opening_values(game))
        fresh = economy_api.backing_marginal_cost(economy_api.blank_economy(setup))
        kept = economy_port_coin._backing_margin(setup)
        self.assertEqual(kept, None if fresh is None else tuple(fresh))
        self.assertEqual(economy_port_coin._backing_margin(setup), kept)


if __name__ == "__main__":
    unittest.main()
