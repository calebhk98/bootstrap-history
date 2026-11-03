"""The unpaid-trade wage rule (sim/economy/trade_wages.py)."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import trade_wages
from sim.economy.market_memory import market_key


def setup(opening=None):
    return types.SimpleNamespace(opening_wages=opening or {}, unskilled_trade="labourer",
                                 trades={"smith": types.SimpleNamespace(training_years=0.0)})


class WageInArea(unittest.TestCase):
    def test_the_area_wage_comes_first(self):
        memory = types.SimpleNamespace(wages={market_key("smith", "north"): 3.0, market_key("labourer", "north"): 1.0})
        self.assertEqual(trade_wages.wage_in_area(setup({"smith": 9.0}), memory, "smith", "north"), 3.0)

    def test_the_opening_wage_prices_an_unpaid_trade(self):
        memory = types.SimpleNamespace(wages={market_key("labourer", "north"): 1.0})
        self.assertEqual(trade_wages.wage_in_area(setup({"smith": 9.0}), memory, "smith", "north"), 9.0)

    def test_no_wage_anywhere_is_none(self):
        memory = types.SimpleNamespace(wages={})
        self.assertIsNone(trade_wages.wage_in_area(setup(), memory, "smith", "north"))


if __name__ == "__main__":
    unittest.main()
