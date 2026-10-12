"""A game opened from a shipped opening is the same game as one that ran the spin-up, and runs no spin-up."""
import os
import random
import tempfile
import unittest
from unittest import mock

from sim.tests import harness  # noqa: F401  (shortens the spin-up for the suite)
from sim.engine import economy_port_year, shipped_openings
from sim.engine.core import Sim
from sim.engine.data import load, load_civ
from sim.engine.state import serialize_state


def _game(nodes):
    game = Sim(nodes, [], random.Random(3), events=False, manual=True, civ=load_civ("rome_100ad"))
    game.done_year = {}
    game.step()
    return game


class ShippedOpeningGameTests(unittest.TestCase):
    def test_a_shipped_opening_gives_the_spun_up_game_without_spinning_up(self):
        _tree, _prices, nodes, _wages, _goods = load()
        with tempfile.TemporaryDirectory() as shipped, tempfile.TemporaryDirectory() as first_cache, \
                tempfile.TemporaryDirectory() as second_cache:
            with mock.patch.object(shipped_openings, "SHIPPED_OPENINGS_DIRECTORY", shipped):
                with mock.patch.object(economy_port_year, "SPIN_UP_CACHE_DIRECTORY", first_cache):
                    spun = _game(nodes)
                    key = spun.economy.agent.opening_cache_key()
                    shipped_openings.write(key, economy_port_year.solve_cache.cached_json(
                        key, lambda: self.fail("the spin-up was not cached"), cache_dir=first_cache))
                with mock.patch.object(economy_port_year, "SPIN_UP_CACHE_DIRECTORY", second_cache), \
                        mock.patch.object(economy_port_year.AgentEconomy, "_spun_up",
                                          side_effect=AssertionError("ran the spin-up")):
                    from_shipped = _game(nodes)
        self.assertEqual(serialize_state(from_shipped.state), serialize_state(spun.state))


if __name__ == "__main__":
    unittest.main()
