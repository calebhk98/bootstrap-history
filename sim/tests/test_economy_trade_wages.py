"""The one wage rule for a trade (sim/economy/trade_wages.py): the market's paid wage, else the opening wage at the price level,
else the unskilled wage plus the training premium."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import trade_wages
from sim.economy.market_memory import MarketMemory, market_key


def setup(opening=None, training_years=0.0):
    return types.SimpleNamespace(opening_wages=opening or {}, unskilled_trade="labourer", currency_id="coin",
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

    def test_a_scope_with_no_opening_wages_prices_on_the_unskilled_wage_alone(self):
        self.assertEqual(trade_wages.priced_trade_wage(setup({"smith": 9.0}), "smith", None, 1.5, None), 1.5)

    def test_no_rule_applying_is_none(self):
        self.assertIsNone(trade_wages.priced_trade_wage(setup(), "smith", None, None, 2.0))


class WageInArea(unittest.TestCase):
    def test_the_areas_paid_wage_and_unskilled_wage_and_the_memorys_price_level_are_read(self):
        memory = types.SimpleNamespace(wages={market_key("labourer", "north"): 1.0}, opening_wage_level=lambda money: 3.0)
        self.assertEqual(trade_wages.wage_in_area(setup({"smith": 2.0}), memory, "smith", "north"), 6.0)
        self.assertEqual(trade_wages.wage_in_area(setup(), memory, "smith", "north"), 1.0)

    def test_no_wage_anywhere_is_none(self):
        memory = types.SimpleNamespace(wages={}, opening_wage_level=lambda money: 1.0)
        self.assertIsNone(trade_wages.wage_in_area(setup(), memory, "smith", "north"))


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
