"""What leaning on a trade does to its price (labour market `price_factor`): none with no pressure, rising with the hours
pressed, falling with the people the local market has of the trade, and saturating at the cap. Called on a stub labour and
world built here with two pool sizes, no game."""
QUICK_TOPIC = True
import types
import unittest

from sim.labour.labour_market_api import LabourMarket

HOURS_PER_PERSON = 2000.0
TRADE = "smith"


class _Market(LabourMarket):
    def standing_draw(self, trade):
        return 0.0


def market(people_in_the_market):
    supply = people_in_the_market * HOURS_PER_PERSON      # the market's supply is in hours a year
    world = types.SimpleNamespace(
        state=types.SimpleNamespace(household=types.SimpleNamespace(labour_pressure_records={}),
                                    scenario=types.SimpleNamespace(year=100)),
        HOURS_PER_PERSON_YEAR=HOURS_PER_PERSON)
    labour = types.SimpleNamespace(_world=world, market_supply=lambda trade: supply)
    return _Market(labour)


class PriceFactorTests(unittest.TestCase):
    def test_a_trade_nobody_has_leaned_on_costs_nothing_extra(self):
        self.assertEqual(market(500).price_factor(TRADE), 1.0)

    def test_pressing_more_hours_raises_the_factor(self):
        factors = []
        for people in (1, 5, 10, 20):
            pressed = market(500)
            pressed.press(TRADE, people * HOURS_PER_PERSON)
            factors.append(pressed.price_factor(TRADE))
        self.assertEqual(factors, sorted(factors))
        self.assertGreater(factors[-1], factors[0])

    def test_the_same_pressure_moves_a_deep_market_less_than_a_shallow_one(self):
        deep, shallow = market(1_000_000), market(50)
        for each in (deep, shallow):
            each.press(TRADE, 10 * HOURS_PER_PERSON)
        self.assertLess(deep.price_factor(TRADE) - 1.0, shallow.price_factor(TRADE) - 1.0)
        self.assertGreater(deep.price_factor(TRADE), 1.0)

    def test_the_factor_saturates_at_the_cap_however_hard_the_trade_is_leaned_on(self):
        crushed = market(1)
        crushed.press(TRADE, 1.0e9)
        capped = 1.0 + LabourMarket.LABOUR_PRICE_PRESSURE_COEFFICIENT * LabourMarket.LABOUR_PRESSURE_SHARE_CAP ** 2
        self.assertAlmostEqual(crushed.price_factor(TRADE), capped)

    def test_pressure_fades_with_the_years(self):
        pressed = market(500)
        pressed.press(TRADE, 10 * HOURS_PER_PERSON)
        now = pressed.price_factor(TRADE)
        pressed._world.state.scenario.year += 3
        self.assertLess(pressed.price_factor(TRADE), now)


if __name__ == "__main__":
    unittest.main()
