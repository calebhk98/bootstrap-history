"""A trade no producer hires is priced from the unskilled wage and its training premium, not from stale seeds;
the credit room the money screen shows is in coin. Each function is called on a stand-in economy built here."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import api
from sim.economy.setup import TradeSpec
from sim.engine import economy_port_year
from sim.engine.economy_port_year import AgentEconomy

SCRIBE, LABOURER, TOWN = "scribe", "labourer", "town"
STALE_SEED_WAGE = 500.0
COIN_PER_UNIT = 2.0


def economy_with_unhired_scribe():
    """A one-country economy whose labourers were hired last year and whose scribes were not (a seed wage stands)."""
    setup = types.SimpleNamespace(
        unskilled_trade=LABOURER, tiles=[TOWN], countries=lambda: ["home"], coin_per_unit=COIN_PER_UNIT,
        trades={LABOURER: TradeSpec(LABOURER), SCRIBE: TradeSpec(SCRIBE, training_years=6.0)})
    record = types.SimpleNamespace(
        memory=types.SimpleNamespace(wages={"%s|work@%s" % (LABOURER, TOWN): 1.2, "%s|work@%s" % (SCRIBE, TOWN): STALE_SEED_WAGE}),
        hours_hired={"%s|work@%s" % (LABOURER, TOWN): 900.0},
        hours_idle={"%s|work@%s" % (LABOURER, TOWN): 100.0, "%s|work@%s" % (SCRIBE, TOWN): 50.0})
    return types.SimpleNamespace(setup=setup, record=record)


def agent_economy_over(economy, wages):
    """An `AgentEconomy` whose year's answers are `wages` (by trade, in coin) over the economy."""
    agent = AgentEconomy.__new__(AgentEconomy)
    agent._economy = economy
    agent.answers = lambda country=None: ({}, wages, 0.05)
    return agent


class UnhiredTradeWageTests(unittest.TestCase):
    def test_weighted_wages_leave_out_a_trade_nobody_hired(self):
        wages = api.wages_by_trade_weighted(economy_with_unhired_scribe())
        self.assertNotIn(SCRIBE, wages)
        self.assertIn(LABOURER, wages)

    def test_unhired_trade_is_priced_from_unskilled_wage_and_premium(self):
        economy = economy_with_unhired_scribe()
        unskilled = 2.4
        agent = agent_economy_over(economy, {LABOURER: unskilled})
        premium = api.trade_premium(economy.setup, SCRIBE)
        self.assertGreater(premium, 0.0)
        self.assertAlmostEqual(agent.wage_per_hour(SCRIBE), unskilled * (1.0 + premium))
        self.assertLess(agent.wage_per_hour(SCRIBE), STALE_SEED_WAGE * COIN_PER_UNIT)


class CreditRoomUnitsTests(unittest.TestCase):
    def test_credit_room_is_in_coin_not_economy_units(self):
        economy = types.SimpleNamespace(setup=types.SimpleNamespace(coin_per_unit=COIN_PER_UNIT))
        agent = AgentEconomy.__new__(AgentEconomy)
        agent._economy = economy
        agent.answers = lambda country=None: ({}, {}, 0.05)
        with mock.patch.object(economy_port_year.economy_api, "credit_room", return_value=150.0) as room:
            self.assertAlmostEqual(agent.credit_room("borrower:a"), 150.0 * COIN_PER_UNIT)
        room.assert_called_once_with(economy, "borrower:a")
        with mock.patch.object(economy_port_year.economy_api, "credit_room", return_value=None):
            self.assertIsNone(agent.credit_room("borrower:a"))


if __name__ == "__main__":
    unittest.main()
