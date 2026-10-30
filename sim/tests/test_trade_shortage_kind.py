"""A project short of a trade is told "booked" only when other work books it;
a trade the society cannot field at that pace is a staffing shortage. Complaint 640: the draw and the note are called
on the projects module over one project and one trade's supply, so no game is built."""
QUICK_TOPIC = True

import types
import unittest

from .harness import *  # noqa: F401,F403
from sim.tests import projects_host

NODE = "mill"
TRADE = "smith"
HOURS_WANTED = 1000.0
YEARS = 2.0
PACE = HOURS_WANTED / YEARS   # hours a year the project asks of the trade


class ProgressGame:
    """One project of one trade, and the hours the society can field of that trade."""

    def __init__(self, supply):
        self.used = {}
        self.project_state = {"lab_left": None, "yrs": 0.0}
        self.module = projects_host.build(
            tree={NODE: {"lab": {TRADE: HOURS_WANTED}, "yrs": YEARS}}, hours_you_can_call_on=lambda trade: supply,
            hour_commitments=lambda: {"trade_hours_used": self.used})
        self.module.needs.send = self.send
        self.module._effective_lab_left = lambda node_id, project_state: {TRADE: HOURS_WANTED}
        self.module.lab_max_span = lambda node_id: 99.0

    def send(self, command):
        self.used[command.trade] = self.used.get(command.trade, 0.0) + command.hours

    def draw(self):
        return self.module.lab_year_draw(NODE, self.project_state, 1.0, 1.0e9)

    def trade_shortfall_note(self, project_state):
        return self.module.trade_shortfall_note(project_state)

    def trade_shortage_kind(self, trade, need, total_demand=None):
        return self.module.trade_shortage_kind(trade, need, total_demand)


class TradeShortageKind(unittest.TestCase):

    def test_alone_and_beyond_supply_is_staffing_not_booked(self):
        game = ProgressGame(supply=0.4 * PACE)
        game.draw()
        note = game.trade_shortfall_note(game.project_state)
        self.assertEqual(game.project_state["short_of_trade_staffing"], [TRADE])
        self.assertNotIn("already booked", note)
        self.assertIn("nobody to do the work", note)
        self.assertIn(TRADE, note)

    def test_booked_by_a_second_project_is_booked(self):
        game = ProgressGame(supply=1.5 * PACE)
        game.used[TRADE] = 1.5 * PACE   # another project took all of it
        game.draw()
        self.assertEqual(game.project_state["short_of_trade"], [TRADE])
        self.assertEqual(game.project_state["short_of_trade_staffing"], [])
        self.assertIn("already booked", game.trade_shortfall_note(game.project_state))

    def test_a_project_the_trade_can_serve_is_not_short(self):
        game = ProgressGame(supply=1.5 * PACE)
        game.draw()
        self.assertEqual(game.project_state["status"], "ACTIVE")
        self.assertNotIn("short_of_trade", game.project_state)

    def test_the_kind_of_a_shortage(self):
        game = ProgressGame(supply=PACE)
        self.assertEqual(game.trade_shortage_kind(TRADE, 2.0 * PACE), "staffing")
        self.assertEqual(game.trade_shortage_kind(TRADE, PACE), "booked")
        self.assertEqual(game.trade_shortage_kind(TRADE, PACE, total_demand=PACE), None)
        self.assertEqual(game.trade_shortage_kind(TRADE, PACE, total_demand=2.0 * PACE), "booked")


if __name__ == "__main__":
    unittest.main()
