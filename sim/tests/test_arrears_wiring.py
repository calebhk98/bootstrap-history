"""Complaint 640: the yearly step's afford gate (`_project_progress_afford_gate`) writes the funding rule's verdict onto
the project: a project owing nothing keeps its hours in arrears, an underfunded one gives hours back, is flagged and
carries the cause. The portfolio rows and the `stuck` screen carry that cause. The funding rule is in
test_arrears_hours and test_arrears_visibility."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import project_funding
from sim.engine.step_phase_projects import ProjectProgressPhaseMixin
from sim.ui.proto import dispatch_inspection_stuck
from sim.ui.proto.dispatch_inspection_stuck import _stuck_work_in_hand
from sim.ui.proto.economy import _portfolio_rows


class Gate(ProjectProgressPhaseMixin):
    def __init__(self, capital):
        self.state = types.SimpleNamespace(household=types.SimpleNamespace(capital=capital))

    def living_cost(self, _rev=None, _upkeep=None):
        return 0.0

    def credit_limit(self, _rev=None, _upkeep=None):
        return 0.0


CONTEXT = {"revenue": 0.0, "upkeep": 0.0, "mine_operating": 0.0}


class AffordGate(unittest.TestCase):
    def _gate(self, capital, money, spent_hours=400.0, offered=500.0, ph_left=100.0, cost_left=None):
        gate = Gate(capital)
        project = {"ph_left": ph_left, "cost_left": money if cost_left is None else cost_left}
        lost = []
        paid, refunded = gate._project_progress_afford_gate("p", project, money, 0.0, spent_hours, offered, lost, CONTEXT)
        return project, paid, refunded, lost

    def test_a_project_owing_nothing_keeps_its_hours_in_arrears_and_is_not_flagged(self):
        project, paid, refunded, lost = self._gate(capital=-1.0, money=0.0, cost_left=0.0)
        self.assertEqual((paid, refunded, lost), (0.0, 0.0, []))
        self.assertEqual(project["ph_left"], 100.0)
        self.assertNotIn("underfunded_this_year", project)

    def test_an_unfunded_bill_in_arrears_gives_hours_back_and_says_why(self):
        project, paid, refunded, lost = self._gate(capital=-100.0, money=500.0)
        self.assertTrue(project["underfunded_this_year"])
        self.assertEqual(project["why_underfunded"], project_funding.WHY_IN_ARREARS)
        self.assertEqual(refunded, 400.0)
        self.assertEqual(project["ph_left"], 100.0 + 400.0)
        self.assertEqual(lost, [("p", 400.0)])

    def test_a_bill_the_purse_covers_clears_an_earlier_flag(self):
        gate = Gate(10000.0)
        project = {"ph_left": 100.0, "cost_left": 500.0, "underfunded_this_year": True, "why_underfunded": "x"}
        gate._project_progress_afford_gate("p", project, 500.0, 0.0, 400.0, 500.0, [], CONTEXT)
        self.assertNotIn("underfunded_this_year", project)
        self.assertNotIn("why_underfunded", project)


class ReplyRelays(unittest.TestCase):
    CAUSE = project_funding.WHY_IN_ARREARS

    def test_the_portfolio_row_carries_the_cause_the_project_was_left_with(self):
        nodes = {"academy": {"yrs": 5.0}}
        rows = _portfolio_rows(nodes, {"academy": {"name": "Academy", "waiting_on": "your hours",
                                                   "why_underfunded": self.CAUSE}})
        self.assertEqual(rows[0]["why_underfunded"], self.CAUSE)

    def test_the_stuck_screen_names_the_cause_and_calls_the_project_money_bound(self):
        sim = types.SimpleNamespace(
            active={"academy": {"cost_left": 100.0, "spent": 0.0, "ph_left": 50.0, "yrs": 0.0,
                                "why_underfunded": self.CAUSE}},
            project_cost=lambda node_id: 100.0, calendar_floor=lambda node_id: 3.0)
        with mock.patch.object(dispatch_inspection_stuck, "_waiting_on", lambda *args: "waiting"):
            reason = _stuck_work_in_hand(sim, {"academy": {}})
        self.assertEqual(reason["each_why_underfunded"], {"academy": self.CAUSE})
        self.assertEqual(reason["each_kind"], {"academy": "money"})


if __name__ == "__main__":
    unittest.main()
