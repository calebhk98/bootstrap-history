"""A way finished mid-game reaches the live economy (`AgentEconomy.sync_ways`): the game's built ways are handed to the economy
and the cached floor costs are dropped, and a game whose economy has not opened hands nothing over. Called on a stand-in."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.markets import agent_economy
from sim.markets.year_figures import YearFigures


def _port(economy):
    port = types.SimpleNamespace(figures=YearFigures(), _economy=economy)
    port.figures.floor_costs = {"wheat": 1.0}
    port._world = types.SimpleNamespace(state=types.SimpleNamespace(economy=types.SimpleNamespace(improvements={("a", "b"): {"road": True}})))
    return port


class SyncWaysTest(unittest.TestCase):
    def test_the_live_economy_is_given_the_built_ways_and_the_floor_costs_are_dropped(self):
        live = object()
        port = _port(live)
        with mock.patch.object(agent_economy.economy_api, "set_improvements") as handed:
            agent_economy.AgentEconomy.sync_ways(port)
        handed.assert_called_once_with(live, {("a", "b"): {"road": True}})
        self.assertEqual(port.figures.floor_costs, {})

    def test_an_economy_not_yet_open_is_handed_nothing(self):
        port = _port(None)
        with mock.patch.object(agent_economy.economy_api, "set_improvements") as handed:
            agent_economy.AgentEconomy.sync_ways(port)
        handed.assert_not_called()
        self.assertEqual(port.figures.floor_costs, {})


if __name__ == "__main__":
    unittest.main()
