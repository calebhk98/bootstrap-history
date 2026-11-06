"""Asking the economy's wage before the game's money is priced answers None and does not open the economy: opening it
prices the money from that wage, so opening on the ask recursed without end (a new game could not start)."""

QUICK_TOPIC = True

import types
import unittest

from sim.markets.agent_views_labour import AgentLabourViews


def views_over(economy):
    views = AgentLabourViews.__new__(AgentLabourViews)
    views.parts = types.SimpleNamespace(market_objects=types.SimpleNamespace(economy=economy))
    return views


class AgentWageBeforeMoneyIsPriced(unittest.TestCase):
    def test_no_wage_and_no_opening_before_the_money_is_priced(self):
        def opens():
            raise AssertionError("the economy was opened by a wage asked before the money is priced")
        economy = types.SimpleNamespace(world=types.SimpleNamespace(money_from_economy=lambda: False), answering=opens)
        self.assertIsNone(views_over(economy).agent_wage_at("labourer", "t1"))

    def test_the_wage_once_the_money_is_priced(self):
        prices = types.SimpleNamespace(wage_per_hour_at=lambda trade, tile: 2.5)
        economy = types.SimpleNamespace(world=types.SimpleNamespace(money_from_economy=lambda: True),
                                        answering=lambda: types.SimpleNamespace(prices=prices))
        self.assertEqual(views_over(economy).agent_wage_at("labourer", "t1"), 2.5)


if __name__ == "__main__":
    unittest.main()
