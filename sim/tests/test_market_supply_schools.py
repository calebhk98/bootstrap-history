"""Trade schools reach the labour market only through the people they train: the hours the labour core offers
(`Supply.market_supply`) do not add the places of a school."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_supply import Supply

HOURS_PER_PERSON = 2000.0


class OfferedSupply(Supply):
    def _hours_offered_in_reach(self, trade):
        return 5000.0

    def people_who_exist(self, trade):
        return 100.0


def supply_with_schools(schools):
    world = types.SimpleNamespace(
        economy=types.SimpleNamespace(agent_working_hours=lambda: HOURS_PER_PERSON),
        workforce=types.SimpleNamespace(trade_schools=schools),
        trades=types.SimpleNamespace(trades_absent=set()),
        actors=types.SimpleNamespace(actor_staff_fte=lambda trade: 0.0))
    trades = types.SimpleNamespace(trade_available=lambda trade: True, LITERATE_TRADES=frozenset())
    return OfferedSupply(world, None, None, None, trades)


class MarketSupplyTests(unittest.TestCase):
    def test_a_trade_school_adds_no_hours_to_what_the_core_offers(self):
        self.assertEqual(supply_with_schools({"smith": 4.0}).market_supply("smith"), 5000.0)

    def test_a_society_with_no_school_offers_the_same(self):
        self.assertEqual(supply_with_schools({}).market_supply("smith"), 5000.0)


if __name__ == "__main__":
    unittest.main()
