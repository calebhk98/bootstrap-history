"""A trade the core holds a wage for is priced at it though nobody hired it; one the core holds no wage for is priced from the
unskilled wage and its training premium;
the credit room the money screen shows is in coin. Each function is called on a stand-in economy built here."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import api
from sim.economy.setup import SetupTrade
from sim.markets.reads_prices import PriceReads
from sim.tests.labour_record_stand_in import labour_record

SCRIBE, LABOURER, TOWN = "scribe", "labourer", "town"
OPENING_WAGE = 500.0
COIN_PER_UNIT = 2.0


def economy_with_unhired_scribe(scribe_wage=None):
    """A one-country economy whose labourers were hired last year and whose scribes were not; `scribe_wage` is the core's
    wage for the scribes (None: the core holds none)."""
    setup = types.SimpleNamespace(
        unskilled_trade=LABOURER, tiles=[TOWN], currency_id="coin", opening_wages={LABOURER: 1.0}, countries=lambda: ["home"], coin_per_unit=COIN_PER_UNIT,
        trades={LABOURER: SetupTrade(LABOURER), SCRIBE: SetupTrade(SCRIBE, training_years=6.0)})
    wages = {"%s|work@%s" % (LABOURER, TOWN): 1.2}
    if scribe_wage is not None:
        wages["%s|work@%s" % (SCRIBE, TOWN)] = scribe_wage
    record = types.SimpleNamespace(
        memory=types.SimpleNamespace(wages=wages, opening_wage_level=lambda currency: 1.0,
                                     holds_wage_for=lambda trade: any(key.startswith(trade + "|") for key in wages)),
        labour=labour_record({"%s|work@%s" % (LABOURER, TOWN): 900.0},
                             {"%s|work@%s" % (LABOURER, TOWN): 100.0, "%s|work@%s" % (SCRIBE, TOWN): 50.0}))
    return types.SimpleNamespace(setup=setup, record=record)


class UnhiredTradeWageTests(unittest.TestCase):
    def test_weighted_wages_hold_a_trade_nobody_hired_at_the_core_wage(self):
        wages = api.wages_by_trade_weighted(economy_with_unhired_scribe(scribe_wage=1.7))
        self.assertEqual(wages[SCRIBE], 1.7)
        self.assertIn(LABOURER, wages)

    def test_weighted_wages_leave_out_a_trade_the_core_holds_no_wage_for(self):
        self.assertNotIn(SCRIBE, api.wages_by_trade_weighted(economy_with_unhired_scribe()))

    def test_unhired_trade_is_priced_from_unskilled_wage_and_premium(self):
        economy = economy_with_unhired_scribe()
        unskilled = 1.2
        premium = api.trade_premium(economy.setup, SCRIBE)
        wage_in_coin = api.country_trade_wage(economy, SCRIBE, None) * api.coin_per_unit(economy)
        self.assertGreater(premium, 0.0)
        self.assertAlmostEqual(wage_in_coin, unskilled * (1.0 + premium) * COIN_PER_UNIT)
        self.assertLess(wage_in_coin, OPENING_WAGE * COIN_PER_UNIT)


class CreditRoomUnitsTests(unittest.TestCase):
    def test_credit_room_is_in_coin_not_economy_units(self):
        economy = types.SimpleNamespace(setup=types.SimpleNamespace(coin_per_unit=COIN_PER_UNIT))
        agent = PriceReads(types.SimpleNamespace(economy=lambda: economy), None)
        agent.answers = lambda country=None: ({}, {}, 0.05)
        with mock.patch.object(api, "credit_room", return_value=150.0) as room:
            self.assertAlmostEqual(agent.credit_room("borrower:a"), 150.0 * COIN_PER_UNIT)
        room.assert_called_once_with(economy, "borrower:a")
        with mock.patch.object(api, "credit_room", return_value=None):
            self.assertIsNone(agent.credit_room("borrower:a"))


if __name__ == "__main__":
    unittest.main()
