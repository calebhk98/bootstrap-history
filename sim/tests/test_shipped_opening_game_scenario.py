"""Scenario: a game opened from shipped cache entries is the same game as one that computed them, and runs no spin-up.
The shipped-entry rules are test_shipped_openings; the spin-up is cut to its shortest so the computed game is cheap."""
import os
import random
import tempfile
import unittest
from unittest import mock

from sim.tests import harness  # noqa: F401  (shortens the spin-up for the suite)
from sim.engine import economy_port_year, shipped_openings, solve_cache
from sim.engine.core import Sim
from sim.engine.data import load, load_civ
from sim.engine.state import serialize_state


def _game(nodes):
    game = Sim(nodes, [], random.Random(3), events=False, manual=True, civ=load_civ("rome_100ad"))
    game.done_year = {}
    game.step()
    return game


class ShippedOpeningGameTests(unittest.TestCase):
    def test_a_shipped_opening_gives_the_computed_game_without_spinning_up(self):
        _tree, _prices, nodes, _wages, _goods = load()
        with tempfile.TemporaryDirectory() as shipped, tempfile.TemporaryDirectory() as first, \
                tempfile.TemporaryDirectory() as second, \
                mock.patch.dict(os.environ, {economy_port_year.SPIN_UP_YEARS_ENV: "1,1"}), \
                mock.patch.object(shipped_openings, "SHIPPED_OPENINGS_DIRECTORY", shipped):
            first_cache = os.path.join(first, "agent_economy")
            with mock.patch.object(economy_port_year, "SPIN_UP_CACHE_DIRECTORY", first_cache), \
                    solve_cache.recording() as touched:
                computed = _game(nodes)
            spin_ups = [key for directory, key in touched if directory == first_cache]
            self.assertEqual(len(spin_ups), 1)
            shipped_openings.write("agent_economy", spin_ups[0], solve_cache.cached_json(
                spin_ups[0], lambda: self.fail("the spin-up was not cached"), first_cache))
            with mock.patch.object(economy_port_year, "SPIN_UP_CACHE_DIRECTORY", os.path.join(second, "agent_economy")), \
                    mock.patch.object(economy_port_year.AgentEconomy, "_spun_up",
                                      side_effect=AssertionError("ran the spin-up")):
                from_shipped = _game(nodes)
        self.assertEqual(serialize_state(from_shipped.state), serialize_state(computed.state))


if __name__ == "__main__":
    unittest.main()
