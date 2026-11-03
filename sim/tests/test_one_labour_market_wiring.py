"""Complaints 358 and 356, the wiring: the world every actor asks reads the one labour market's rate, and the rate a hire quote
promises from next year is what the market then quotes once the hire is on the books. Called on a stand-in market and world; no
game is built. The market's own arithmetic is in test_one_labour_market."""
import types
import unittest

from sim.actors.world import ActorWorld
from sim.tests.world_stand_in import fake_needs
from sim.labour.labour_market_api import LabourMarket

QUICK_TOPIC = True
UNDER_TEST = {"hire"}

TRADE = "artisan"
HOURS_PER_YEAR = 2000.0
SUPPLY = 10_000.0
RATES = {"artisan": 0.9, "labourer": 0.4, "scribe": 1.1}


def real_market(pressure=None, employed=None):
    employed = dict(employed or {})
    world = types.SimpleNamespace(
        workforce=types.SimpleNamespace(worker_housing_places=None),
        year=0, state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=0)),
        HOURS_PER_PERSON_YEAR=HOURS_PER_YEAR, price_index=1.5, wage_index=1.3,
        economy=types.SimpleNamespace(agent_wage_per_hour=lambda trade: None), real_output_per_head=lambda: 1.1,
        wages={}, actor_staff_fte=lambda name: 0.0)
    labour = types.SimpleNamespace(
        _world=world, wage_schedule=lambda: types.SimpleNamespace(training_years={}),
        market_supply=lambda trade: SUPPLY + HOURS_PER_YEAR * employed.get(trade, 0.0),
        employed=lambda trade: employed.get(trade, 0.0),
        set_employed=lambda trade, people: employed.__setitem__(trade, people),
        base_annual_wage=lambda trade: 100.0, wage_cost_factors=lambda trade: {"weighted": 1.2},
        LABOUR_PAY_SHARE_OF_OUTPUT_GAIN=1.0)
    return LabourMarket(labour), labour


class HireQuoteTests(unittest.TestCase):
    def test_the_wage_quoted_does_not_depend_on_how_many_are_taken_on_or_how_hard_the_trade_is_leaned_on(self):
        market, _labour = real_market()
        calm, _labour = real_market()
        self.assertEqual(market.quote_annual(TRADE), market.quote_annual(TRADE))
        self.assertEqual(market.quote_annual(TRADE), calm.quote_annual(TRADE))


class WorldReadsTheOneMarketTests(unittest.TestCase):
    def world(self):
        market = types.SimpleNamespace(
            quote=lambda trade, hours=0.0: RATES[trade],
            quote_annual=lambda trade, people=0.0: RATES[trade] * HOURS_PER_YEAR)
        needs = fake_needs(labour_market=market, trade_registry=lambda: {"labourer": {"fallback": True}}, hours_per_person_year=HOURS_PER_YEAR,
                           concern_staff=lambda node_id: {"artisan": 2.0, "scribe": 1.0})
        return ActorWorld(types.SimpleNamespace(needs=needs)), market

    def test_the_world_hands_every_actor_the_one_market(self):
        world, market = self.world()
        self.assertIs(world.labour.labour_market, market)

    def test_a_person_years_pay_and_an_hours_pay_are_the_markets_quote(self):
        world, _market = self.world()
        self.assertEqual(world.labour.pay_per_person_year(TRADE), RATES[TRADE] * HOURS_PER_YEAR)
        self.assertEqual(world.labour.hourly_pay(TRADE), RATES[TRADE])

    def test_a_concerns_wage_bill_is_its_crew_at_the_markets_quotes(self):
        world, _market = self.world()
        expected = 2.0 * RATES["artisan"] * HOURS_PER_YEAR + 1.0 * RATES["scribe"] * HOURS_PER_YEAR
        self.assertAlmostEqual(world.concerns.concern_wage_bill("any_works"), expected)

    def test_the_labourers_annual_wage_is_the_markets_quote_for_a_labourer(self):
        world, _market = self.world()
        self.assertEqual(world.groups._annual_labourer_wage(), RATES["labourer"] * HOURS_PER_YEAR)


if __name__ == "__main__":
    unittest.main()
