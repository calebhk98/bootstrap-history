"""sim/economy/api.py: its accessors agree with reading the record directly. The wall (every outside import is published) is
test_economy_api_wall.py."""
QUICK_TOPIC = True

import unittest

from sim.economy import api
from sim.tests import economy_fixture


class EconomyApiTests(unittest.TestCase):
    def test_accessors_match_direct_reads(self):
        economy, _outcomes = economy_fixture.run(years=1)
        record, money = economy.record, economy.setup.currency_id
        self.assertEqual(api.opening_quantities(economy), record.opening_basket)
        self.assertEqual(api.producers_of(economy), record.producers)
        self.assertEqual(api.interest_rate(economy), record.memory.rates.get(money))
        self.assertEqual(api.external_trade_net(economy), record.book.edge_net(api.EDGE_EXTERNAL, money))
        self.assertEqual(api.external_trade_volume(economy), record.book.edge_volume(api.EDGE_EXTERNAL, money))
        for agent in sorted(record.producers):
            self.assertEqual(api.account_balance(economy, agent), record.book.balance(agent, money))
            self.assertEqual(api.account_holdings(economy, agent), record.book.holdings(agent))
        volumes = {}
        for key, volume in record.volumes.items():
            good = key.split("|", 1)[0]
            volumes[good] = volumes.get(good, 0.0) + volume
        self.assertEqual(api.traded_volumes(economy), volumes)
        self.assertTrue(volumes)
        wages = {}
        for key, wage in record.memory.wages.items():
            wages.setdefault(key.split("|", 1)[0], []).append(wage)
        self.assertEqual(api.wages_by_trade(economy), wages)
        self.assertTrue(wages)



if __name__ == "__main__":
    unittest.main()
