"""The one wage rule for a trade (sim/economy/trade_wages.py): the market's paid wage, else the opening wage at the price level,
else the unskilled wage plus the training premium, else the opening unskilled wage in today's money plus the premium. The home
country always has a wage; a partner country has none when its markets paid neither the trade nor the unskilled one."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import trade_wages
from sim.economy.market_memory import MarketMemory, market_key


def setup(opening=None, training_years=0.0):
    return types.SimpleNamespace(opening_wages={"labourer": 1.0, **(opening or {})}, unskilled_trade="labourer", currency_id="coin",
                                 trades={"smith": types.SimpleNamespace(training_years=training_years)})


class PricedTradeWage(unittest.TestCase):
    def test_a_paid_wage_comes_first_whatever_it_is(self):
        self.assertEqual(trade_wages.priced_trade_wage(setup({"smith": 9.0}), "smith", 3.0, 1.0, 2.0), 3.0)
        self.assertEqual(trade_wages.priced_trade_wage(setup({"smith": 9.0}), "smith", 0.0, 1.0, 2.0), 0.0)

    def test_the_opening_wage_is_scaled_by_the_price_level(self):
        self.assertEqual(trade_wages.priced_trade_wage(setup({"smith": 9.0}), "smith", None, 1.0, 2.0), 18.0)

    def test_without_an_opening_wage_the_unskilled_wage_stands_for_a_trade_with_no_training(self):
        self.assertEqual(trade_wages.priced_trade_wage(setup(), "smith", None, 1.5, 2.0), 1.5)

    def test_without_an_opening_wage_training_adds_its_premium_to_the_unskilled_wage(self):
        wage = trade_wages.priced_trade_wage(setup(training_years=5.0), "smith", None, 1.5, 2.0)
        self.assertGreater(wage, 1.5)

    def test_the_home_scope_with_no_unskilled_wage_prices_on_the_opening_unskilled_wage_in_todays_money(self):
        self.assertEqual(trade_wages.priced_trade_wage(setup(), "smith", None, None, 2.0), 2.0)
        wage = trade_wages.priced_trade_wage(setup(training_years=5.0), "smith", None, None, 2.0)
        self.assertGreater(wage, 2.0)

    def test_the_home_scope_is_never_none(self):
        self.assertIsNotNone(trade_wages.priced_trade_wage(setup(), "smith", None, None, 1.0))

    def test_an_area_with_no_recorded_wage_at_all_is_still_priced(self):
        self.assertEqual(trade_wages.priced_trade_wage(setup({"smith": 9.0}), "smith", None, None, 1.5), 13.5)

    def test_an_unknown_trade_is_an_error_not_an_unskilled_wage(self):
        with self.assertRaises(KeyError):
            trade_wages.priced_trade_wage(setup(), "glassblower", None, 1.5, 1.0)


class WageInArea(unittest.TestCase):
    def test_the_areas_paid_wage_and_unskilled_wage_and_the_memorys_price_level_are_read(self):
        memory = types.SimpleNamespace(wages={market_key("labourer", "north"): 1.0}, opening_wage_level=lambda money: 3.0)
        self.assertEqual(trade_wages.wage_in_area(setup({"smith": 2.0}), memory, "smith", "north"), 6.0)
        self.assertEqual(trade_wages.wage_in_area(setup(), memory, "smith", "north"), 1.0)

    def test_no_wage_recorded_anywhere_still_prices_on_the_opening_wages(self):
        memory = types.SimpleNamespace(wages={}, opening_wage_level=lambda money: 1.0)
        self.assertEqual(trade_wages.wage_in_area(setup(), memory, "smith", "north"), 1.0)
        self.assertEqual(trade_wages.wage_in_area(setup({"smith": 4.0}), memory, "smith", "north"), 4.0)


class RebaseKeepsOpeningWagesInTodaysMoney(unittest.TestCase):
    def test_a_rebase_moves_the_reset_level_into_the_opening_wage_level(self):
        memory = MarketMemory(price_levels={"coin": 1.5})
        memory.rebase_price_levels("coin")
        self.assertEqual(memory.price_levels["coin"], 1.0)
        self.assertEqual(memory.opening_wage_level("coin"), 1.5)
        memory.price_levels["coin"] = 1.2
        self.assertAlmostEqual(memory.opening_wage_level("coin"), 1.8)


class FacedWage(unittest.TestCase):
    def test_a_household_faces_the_recorded_wage_else_its_reservation(self):
        self.assertEqual(trade_wages.faced_wage(2.0, 0.5), 2.0)
        self.assertEqual(trade_wages.faced_wage(None, 0.5), 0.5)


if __name__ == "__main__":
    unittest.main()
