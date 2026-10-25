"""sim/economy/api.py: each accessor agrees with reading the record it is given."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy import api


class StubBook:
    def edge_net(self, edge, money):
        return ("net", edge, money)

    def edge_volume(self, edge, money):
        return ("volume", edge, money)

    def balance(self, agent, money):
        return ("balance", agent, money)

    def holdings(self, agent):
        return ("holdings", agent)


def stand_in(**record_fields):
    setup = types.SimpleNamespace(currency_id="coin", civ_id="home", unskilled_trade="labourer",
                                  countries=lambda: ("home",))
    return types.SimpleNamespace(setup=setup, record=types.SimpleNamespace(book=StubBook(), **record_fields))


class EconomyApiTests(unittest.TestCase):
    def test_opening_quantities_is_a_copy_of_the_opening_basket(self):
        basket = {"grain": 3.0, "ore": 1.0}
        economy = stand_in(opening_basket=basket)
        self.assertEqual(api.opening_quantities(economy), basket)
        self.assertIsNot(api.opening_quantities(economy), basket)

    def test_producers_of_lists_every_producer_when_one_country_is_held(self):
        producers = {"a": types.SimpleNamespace(tile="x"), "b": types.SimpleNamespace(tile="y")}
        self.assertEqual(api.producers_of(stand_in(producers=producers)), producers)

    def test_interest_rate_reads_the_currencys_rate_and_is_none_without_one(self):
        economy = stand_in(memory=types.SimpleNamespace(rates={"coin": 0.07}))
        self.assertEqual(api.interest_rate(economy), 0.07)
        self.assertIsNone(api.interest_rate(stand_in(memory=types.SimpleNamespace(rates={}))))

    def test_external_trade_net_reads_the_external_edge(self):
        self.assertEqual(api.external_trade_net(stand_in()), ("net", api.EDGE_EXTERNAL, "coin"))

    def test_external_trade_volume_reads_the_external_edge(self):
        self.assertEqual(api.external_trade_volume(stand_in()), ("volume", api.EDGE_EXTERNAL, "coin"))

    def test_account_balance_reads_the_currency_balance(self):
        self.assertEqual(api.account_balance(stand_in(), "agent"), ("balance", "agent", "coin"))

    def test_account_holdings_reads_the_books_holdings(self):
        self.assertEqual(api.account_holdings(stand_in(), "agent"), ("holdings", "agent"))

    def test_traded_volumes_sum_each_good_over_its_markets(self):
        economy = stand_in(volumes={"grain|north": 2.0, "grain|south": 3.0, "ore|north": 5.0})
        self.assertEqual(api.traded_volumes(economy), {"grain": 5.0, "ore": 5.0})

    def test_wages_by_trade_lists_each_trades_market_wages(self):
        economy = stand_in(memory=types.SimpleNamespace(wages={"smith|north": 2.0, "smith|south": 3.0, "miner|north": 1.0}))
        self.assertEqual(api.wages_by_trade(economy), {"smith": [2.0, 3.0], "miner": [1.0]})


if __name__ == "__main__":
    unittest.main()
