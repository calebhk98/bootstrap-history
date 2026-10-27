"""What a project is waiting on, and the arrears and market-squeeze lines of the state and money screens
(Complaints 240, 214, 216). Each is called on a stub game or a reply the test builds."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.tests.harness import NODES, ORDER
from sim.ui.proto.render_screen_state import render_state
from sim.ui.proto.render_screens_economy import render_money
from sim.ui.proto.state_waiting import _waiting_on
from sim.tests.ui_stand_in import Game


class WaitingOn(unittest.TestCase):

    def setUp(self):
        self.game = Game(trade_demand_vs_supply=lambda: {}, labour=Game(hours_you_can_call_on=lambda trade: 0.0, director_pool=lambda: 5000.0,
                                                           director_hours_committed=lambda: 0.0),
                                    trade_shortage_kind=lambda trade, need, demand: None,
                                    peek_project_resource_throttle=lambda node_id: (1.0, None),
                                    hour_standing=lambda node_id: None)
        self.calendar_id = next(node_id for node_id in ORDER if NODES[node_id]["yrs"] >= 3 and not NODES[node_id]["lab"])

    def test_waiting_on_the_calendar_says_how_many_years_are_left(self):
        text = _waiting_on(self.game, NODES, self.calendar_id, {"ph_left": 0.0, "yrs": 1.0, "lab_left": {}}, 0.0)
        # presentation: the sentence names the years left
        self.assertTrue(text.startswith("the calendar"), text)
        self.assertIn(str(int(NODES[self.calendar_id]["yrs"]) - 1), text)

    def test_waiting_on_hours_says_how_many_are_still_needed(self):
        text = _waiting_on(self.game, NODES, self.calendar_id, {"ph_left": 1234.0, "yrs": 0.0, "lab_left": {}}, 0.0)
        # presentation: the hours are written with a thousands separator
        self.assertIn("1,234", text)


class Screens(unittest.TestCase):

    def test_the_state_screen_prints_a_sustainable_debt_line_when_in_arrears(self):
        reply = {"capital": -5000.0, "sustainable_debt": 1200.0, "sustainable_debt_means": ""}
        # presentation: the arrears line
        self.assertIn("ustainable debt", render_state(reply))

    def test_the_state_screen_prints_no_such_line_when_in_credit(self):
        reply = {"capital": 5000.0, "sustainable_debt": 1200.0, "sustainable_debt_means": ""}
        # presentation: the arrears line
        self.assertNotIn("ustainable debt at your recurring surplus", render_state(reply))

    def test_the_money_screen_prints_the_itemised_deduction(self):
        reply = {"capital": 1000.0, "where_the_money_comes_from": {"farm": 10.0}, "where_the_market_squeeze_falls": [
            {"category": "grain", "nominal": 3.0, "absorbed": 2.0, "lost": 1.0, "concerns": ["farm"]}]}
        # presentation: the heading of the itemised deduction
        self.assertIn("by category", render_money(reply))


if __name__ == "__main__":
    unittest.main()
