"""Complaint 640: the `labour <trade>` command shows the wage foundation. The arithmetic is called on built prices in
test_dynamic_wages; here the handler is called on a stand-in sim and each component of its reply is the stand-in's reading."""
QUICK_TOPIC = True

import unittest

from sim.ui.proto.dispatch_labour import _cmd_labour
from sim.tests.ui_stand_in import Game


class StandInMarket:
    def quote_annual(self, trade):
        return 100.0

    def cost_factors(self, trade):
        return {"food": 1.1, "housing": 1.2, "tools": 1.3, "skill_and_difficulty": 1.4}

    def unscarce_annual(self, trade):
        return 80.0


def stand_in_labour_views():
    """The workforce views the `labour <trade>` command reads, answered with fixed figures."""
    return dict(
        literate_trades=(), labour_market=StandInMarket(), base_annual_wage=lambda trade: 70.0, wage=lambda trade: 0.05,
        hours_reserved=lambda trade: 0.0, market_supply=lambda trade: 1000.0,
        hours_you_can_call_on=lambda trade: 1000.0, trade_available=lambda trade: True)


class LabourCommandTests(unittest.TestCase):
    def test_detail_carries_every_wage_component_the_sim_reports(self):
        sim = Game(staff={"employees": {}}, staff_wanted={}, trade_spread={"created": set(), "absent": [], "endemic": set(), "introduced_year": {}}, price_index=2.0, **stand_in_labour_views())
        detail = _cmd_labour(sim, {}, {"cmd": "labour", "trade": "smith"}, False)
        foundation = detail["trade"]["wage_foundation"]
        self.assertEqual(foundation["base_for_skill_and_difficulty"], 70.0)
        self.assertEqual({key: foundation[key] for key in ("food", "housing", "tools", "skill_and_difficulty")},
                         {"food": 1.1, "housing": 1.2, "tools": 1.3, "skill_and_difficulty": 1.4})
        self.assertNotIn("demographic_scarcity", foundation)


if __name__ == "__main__":
    unittest.main()
