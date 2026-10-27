"""SMOKE: one unopened Rome game hands the agent economy its built ways, trades and goods (the port), and its portfolio reply is built from its active projects. The rules (carriage table, setup keys, data shape, grouping, paging) are test_economy_built_ways,
test_port_trade_and_goods_data, test_port_unskilled_trade, test_portfolio_bottlenecks and test_portfolio_scale_stuck_advice. No years run."""
import json
import os
import unittest

from sim.markets import port_setup
from sim.geography import api as geography_api
from sim.tests.harness import NODES, S, unopened_sim

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "world")


def _ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


class PortHandsTheEconomyTheGamesData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = unopened_sim()
        cls.setup = port_setup.build_setup(cls.game.economy.world)

    def test_a_game_with_nothing_built_hands_the_economy_no_ways_and_a_road_is_priced_below_a_track(self):
        self.assertEqual(self.setup.improvements, {})
        carriage = port_setup.opening_values(self.game.economy.world)["carriage"]
        self.assertGreater(carriage["road"], 0.0)
        self.assertLess(carriage["road"], carriage["cart"])

    def test_a_built_way_reaches_the_setup(self):
        tiles = sorted(self.setup.tiles)
        pair = next((tile, other) for tile in tiles for other in self.setup.tiles[tile].borders if other in self.setup.tiles)
        edge = geography_api.edge_key(*pair)
        self.game.state.economy.improvements = {edge: {"road": True}}
        self.assertEqual(port_setup.build_setup(self.game.economy.world).improvements, {edge: {"road": True}})
        self.game.state.economy.improvements = {}

    def test_each_trade_carries_its_stated_risk_and_each_durable_good_its_stated_service_life(self):
        with open(os.path.join(DATA, "trades.json"), encoding="utf-8") as handle:
            trades = json.load(handle)["trades"]
        with open(os.path.join(DATA, "service_lives.json"), encoding="utf-8") as handle:
            lives = json.load(handle)["years"]
        for name, trade in trades.items():
            self.assertEqual(self.setup.trades[name].fatality_risk_per_year, trade["fatality_risk_per_year"], name)
        durable = [good for good in lives if good in self.setup.specs]
        self.assertTrue(durable)
        for good in durable:
            self.assertEqual(self.setup.specs[good].service_life_years, lives[good]["years"], good)
        self.assertEqual(self.setup.specs["wheat_kg"].service_life_years, 0.0)

    def test_the_setup_carries_the_unskilled_trade_the_registry_names(self):
        self.assertEqual(self.setup.unskilled_trade, port_setup.opening_values(self.game.economy.world)["unskilled_trade"])
        self.assertIn(self.setup.unskilled_trade, self.setup.opening_wages)


class PortfolioGroupsEveryActiveProject(unittest.TestCase):
    def test_every_active_project_is_in_exactly_one_bottleneck_group(self):
        game = unopened_sim(capital=5_000_000.0)
        for node_id in list(game.order):
            if len(game.active) >= 6:
                break
            if node_id not in game.done and game.can_start(node_id):
                self.assertTrue(_ask(game, cmd="start", id=node_id).get("ok"), node_id)
        self.assertGreaterEqual(len(game.active), 3)
        groups = _ask(game, cmd="portfolio").get("bottlenecks")
        self.assertTrue(groups)
        self.assertEqual(sorted(project for group in groups for project in group["projects"]), sorted(game.active))


if __name__ == "__main__":
    unittest.main()
