"""AgentEconomy.economy takes the opening's record from the disk cache (so from an entry shipped with the checkout)
before spinning up, and AgentEconomy.answers states the economy's prices and wages in coin. Both run on a stand-in
game and a stand-in economy API; the cache rules are test_shipped_openings."""
QUICK_TOPIC = True

import os
import tempfile
import types
import unittest
from unittest import mock

from sim.engine import economy_port_year, shipped_openings
from sim.engine.economy_port_year import AgentEconomy

CACHE_KEY = "opening-key"


def _stand_in_game():
    adopted = []
    purses = types.SimpleNamespace(adopt_book=lambda book, contracts: adopted.append((book, contracts)))
    state = types.SimpleNamespace(economy=types.SimpleNamespace(agent_economy={}), actors=types.SimpleNamespace(purses=purses))
    return types.SimpleNamespace(state=state, civ={"id": "home"}), adopted


class OpeningRecordTests(unittest.TestCase):
    def setUp(self):
        self.shipped = tempfile.TemporaryDirectory()
        self.cache = tempfile.TemporaryDirectory()
        self.addCleanup(self.shipped.cleanup)
        self.addCleanup(self.cache.cleanup)
        self.game, self.adopted = _stand_in_game()
        self.agent = AgentEconomy(self.game)
        self.agent._save = lambda: None
        self.agent.sync_ways = lambda: None
        self.spun_up = []
        self.agent._spun_up = lambda setup: self.spun_up.append(setup) or {"spun": True}
        for patcher in (
                mock.patch.object(shipped_openings, "SHIPPED_OPENINGS_DIRECTORY", self.shipped.name),
                mock.patch.object(economy_port_year, "SPIN_UP_CACHE_DIRECTORY", os.path.join(self.cache.name, "agent_economy")),
                mock.patch.object(economy_port_year, "opening_values", lambda game: {"values": 1}),
                mock.patch.object(economy_port_year, "priced_at_the_margin", lambda game, values: values),
                mock.patch.object(economy_port_year, "build_setup", lambda game, opening: ("setup", opening)),
                mock.patch.object(economy_port_year, "_spin_up_cache_key", lambda setup: CACHE_KEY),
                mock.patch.object(economy_port_year.economy_api, "economy_from_record", lambda setup, record: ("economy", record)),
                mock.patch.object(economy_port_year.economy_api, "economy_book", lambda economy: "book"),
                mock.patch.object(economy_port_year.economy_api, "economy_contracts", lambda economy: "contracts")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_a_shipped_record_opens_the_economy_without_spinning_up(self):
        shipped_openings.write("agent_economy", CACHE_KEY, {"shipped": True})
        economy = self.agent.economy()
        self.assertEqual(economy, ("economy", {"shipped": True}))
        self.assertEqual(self.spun_up, [])

    def test_the_opening_is_kept_and_the_purses_adopt_the_economys_book(self):
        shipped_openings.write("agent_economy", CACHE_KEY, {"shipped": True})
        self.agent.economy()
        self.assertEqual(self.game.state.economy.agent_economy["opening"], {"values": 1})
        self.assertEqual(self.adopted, [("book", "contracts")])

    def test_with_nothing_shipped_the_economy_spins_up_once_and_the_record_is_cached(self):
        self.assertEqual(self.agent.economy(), ("economy", {"spun": True}))
        self.assertEqual(len(self.spun_up), 1)
        self.agent._economy = None
        self.agent._built_from = None
        self.assertEqual(self.agent.economy(), ("economy", {"spun": True}))
        self.assertEqual(len(self.spun_up), 1)


class AnswersTests(unittest.TestCase):
    COIN = 4.0

    def setUp(self):
        self.game, _adopted = _stand_in_game()
        self.agent = AgentEconomy(self.game)
        self.agent._economy = types.SimpleNamespace(setup=types.SimpleNamespace(
            coin_per_unit=self.COIN, countries=lambda: ["home", "abroad"]))
        self.agent.economy = lambda: self.agent._economy
        self.agent._built_from = self.agent.stored
        api = economy_port_year.economy_api
        for patcher in (
                mock.patch.object(api, "wages_by_trade_weighted", lambda economy, country=None: {"smith": 2.0, "weaver": 0.5}),
                mock.patch.object(api, "shown_prices_of", lambda economy, country=None: ({"iron": 3.0}, {"salt"})),
                mock.patch.object(api, "interest_rate", lambda economy: 0.07)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_prices_and_wages_are_the_apis_in_coin_and_the_rate_is_unchanged(self):
        prices, wages, rate = self.agent.answers()
        self.assertEqual(prices, {"iron": 3.0 * self.COIN})
        self.assertEqual(wages, {"smith": 2.0 * self.COIN, "weaver": 0.5 * self.COIN})
        self.assertEqual(rate, 0.07)

    def test_the_goods_without_a_market_price_are_the_stale_ones(self):
        self.agent.answers()
        self.assertEqual(self.agent.stale_goods(), {"salt"})

    def test_answers_are_built_once_until_the_stored_economy_is_replaced(self):
        first = self.agent.answers()
        self.assertIs(self.agent.answers(), first)
        self.agent._built_from = None
        self.assertIsNot(self.agent.answers(), first)


if __name__ == "__main__":
    unittest.main()
