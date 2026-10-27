"""Complaint 640: the `labour <trade>` command shows the wage foundation. The arithmetic is called on built prices in
test_dynamic_wages; here the handler is called on a stand-in sim and each component of its reply is the stand-in's reading."""
QUICK_TOPIC = True

import types
import unittest

from sim.ui.proto.dispatch_labour import _cmd_labour
from sim.tests.ui_stand_in import Game


class StandInMarket:
    def price_factor(self, trade):
        return 1.25

    def quote_annual(self, trade):
        return 100.0

    def cost_factors(self, trade):
        return {"food": 1.1, "housing": 1.2, "tools": 1.3, "skill_and_difficulty": 1.4}

    def in_current_money(self, amount):
        return amount

    def price_factor_after(self, trade, hires):
        return 1.0

    def unscarce_annual(self, trade):
        return 80.0


class StandInLabour:
    LITERATE_TRADES = ()
    market = StandInMarket()

    def base_annual_wage(self, trade):
        return 70.0

    def wage_per_hour(self, trade):
        return 0.05

    def market_supply_split(self, trade):
        return (1000.0, 0.0)

    def hours_reserved(self, trade):
        return 0.0

    def market_supply(self, trade):
        return 1000.0

    def hours_you_can_call_on(self, trade):
        return 1000.0

    def trade_available(self, trade):
        return True


class LabourCommandTests(unittest.TestCase):
    def test_detail_carries_every_wage_component_the_sim_reports(self):
        sim = Game(labour=StandInLabour(), view=lambda name: (lambda: {"employees": {}, "created": set()}), wage_index=1.5, price_index=2.0)
        detail = _cmd_labour(sim, {}, {"cmd": "labour", "trade": "smith"}, False)
        foundation = detail["trade"]["wage_foundation"]
        self.assertEqual(foundation["base_for_skill_and_difficulty"], 70.0)
        self.assertEqual({key: foundation[key] for key in ("food", "housing", "tools", "skill_and_difficulty")},
                         {"food": 1.1, "housing": 1.2, "tools": 1.3, "skill_and_difficulty": 1.4})
        self.assertEqual(foundation["demographic_scarcity"], 1.5)
        self.assertEqual(foundation["local_trade_scarcity"], 1.25)
        self.assertEqual(foundation["society_price_level"], 2.0)


if __name__ == "__main__":
    unittest.main()
