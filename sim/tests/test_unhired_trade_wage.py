"""A trade no producer hires is priced from the unskilled wage and its training premium, not from stale seeds;
the credit room the money screen shows is in coin."""

QUICK_TOPIC = True

import dataclasses
import types
import unittest

from sim.economy import api
from sim.economy.setup import TradeSpec
from sim.engine.economy_port_year import AgentEconomy
from sim.tests import economy_fixture

SCRIBE = "scribe"
STALE_SEED_WAGE = 500.0


def economy_with_unhired_scribe():
    setup = economy_fixture.small_setup()
    trades = dict(setup.trades)
    trades[SCRIBE] = TradeSpec(SCRIBE, training_years=6.0)
    setup = dataclasses.replace(setup, trades=trades)
    economy, _outcomes = economy_fixture.run(setup, years=3)
    economy.record.memory.wages["%s|%s" % (SCRIBE, economy_fixture.TOWN)] = STALE_SEED_WAGE
    return economy


def agent_economy_over(economy):
    stored = {"on": True}
    state = types.SimpleNamespace(economy=types.SimpleNamespace(agent_economy=stored))
    agent = AgentEconomy(types.SimpleNamespace(state=state))
    agent._economy, agent._built_from = economy, stored
    return agent


class UnhiredTradeWageTests(unittest.TestCase):
    def setUp(self):
        self.economy = economy_with_unhired_scribe()

    def test_weighted_wages_leave_out_a_trade_nobody_hired(self):
        self.assertNotIn(SCRIBE, api.wages_by_trade_weighted(self.economy))

    def test_unhired_trade_is_priced_from_unskilled_wage_and_premium(self):
        agent = agent_economy_over(self.economy)
        unskilled = agent.wage_per_hour(self.economy.setup.unskilled_trade)
        premium = api.trade_premium(self.economy.setup, SCRIBE)
        self.assertGreater(premium, 0.0)
        self.assertAlmostEqual(agent.wage_per_hour(SCRIBE), unskilled * (1.0 + premium))
        self.assertLess(agent.wage_per_hour(SCRIBE), STALE_SEED_WAGE * self.economy.setup.coin_per_unit)


class CreditRoomUnitsTests(unittest.TestCase):
    def setUp(self):
        economy_fixture.households_with_a_surplus(self)       # savings are on offer only where households have a surplus

    def test_credit_room_is_in_coin_not_economy_units(self):
        economy, _outcomes = economy_fixture.run(years=3)
        units = api.credit_room(economy, "borrower:a")
        self.assertIsNotNone(units)
        self.assertGreater(units, 0.0)
        room = agent_economy_over(economy).credit_room("borrower:a")
        self.assertAlmostEqual(room, units * economy.setup.coin_per_unit)


if __name__ == "__main__":
    unittest.main()
