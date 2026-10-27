"""The reasons `stuck` gives (`dispatch_inspection_stuck`): nothing started, work in hand, arrears, and a shut concern that is
advised to be opened only when `open` would be accepted. Each builder is called on a stand-in game carrying what it reads."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.refusal import Refusal
from sim.ui.proto import dispatch_inspection_stuck as stuck
from sim.tests.ui_stand_in import Game


def _game(**members):
    training = members.pop("training", [])
    base = dict(active={}, view=lambda name: (lambda: training), capital=1000.0, civ={}, done=set(), operating=set(), project_cost=lambda node_id: 10.0)
    base.update(members)
    return Game(**base)


class StartedNothingTest(unittest.TestCase):
    def test_nothing_in_hand_says_so_and_names_the_cheapest_affordable_start(self):
        reason = stuck._stuck_started_nothing(_game(project_cost=lambda node_id: {"dear": 50.0, "cheap": 5.0}[node_id]),
                                              ["dear", "cheap"], ["cheap"])
        self.assertEqual((reason["what"], reason["kind"]), ("you have started nothing", "idle"))
        self.assertIn("'start cheap'", reason["why"])

    def test_nothing_startable_names_no_start(self):
        reason = stuck._stuck_started_nothing(_game(), [], [])
        self.assertEqual(reason["what"], "you have started nothing")
        self.assertNotIn("'start ", reason["why"])

    def test_a_saving_plan_names_no_start(self):
        self.assertNotIn("'start ", stuck._stuck_started_nothing(_game(), ["a"], ["a"], saving=True)["why"])

    def test_work_or_training_in_hand_is_not_nothing(self):
        self.assertIsNone(stuck._stuck_started_nothing(_game(active={"a": {}}), ["a"], ["a"]))
        self.assertIsNone(stuck._stuck_started_nothing(_game(training=[object()]), ["a"], ["a"]))


class WorkInHandTest(unittest.TestCase):
    def test_each_project_is_listed_with_what_it_waits_on_and_money_when_it_is_underfunded(self):
        active = {"funded": {"spent": 0.0, "ph_left": 5.0, "yrs": 0.0},
                  "short": {"spent": 0.0, "ph_left": 5.0, "yrs": 0.0, "why_underfunded": "in arrears"}}
        game = _game(active=active, calendar_floor=lambda node_id: 1.0)
        with mock.patch.object(stuck, "_waiting_on", lambda sim, nodes, node_id, progress, bill: "waiting on %s" % node_id):
            reason = stuck._stuck_work_in_hand(game, {})
        self.assertEqual(reason["how_many"], 2)
        self.assertEqual(reason["each_kind"], {"funded": "active", "short": "money"})
        self.assertEqual(reason["each_waiting_on"]["short"], "waiting on short")
        self.assertEqual(reason["each_why_underfunded"], {"short": "in arrears"})

    def test_a_project_with_all_its_work_done_and_years_still_to_wait_is_calendar_bound(self):
        game = _game(active={"slow": {"spent": 0.0, "ph_left": 0.0, "yrs": 1.0}}, calendar_floor=lambda node_id: 3.0)
        with mock.patch.object(stuck, "_waiting_on", lambda *arguments: "the calendar"):
            self.assertEqual(stuck._stuck_work_in_hand(game, {})["each_kind"], {"slow": "calendar"})

    def test_no_work_in_hand_is_no_reason(self):
        self.assertIsNone(stuck._stuck_work_in_hand(_game(), {}))


class ArrearsTest(unittest.TestCase):
    def test_a_negative_balance_names_arrears_as_a_money_stall(self):
        game = _game(capital=-100.0, credit_limit=lambda: 500.0, debt_interest_rate=lambda: 0.1)
        reason = stuck._stuck_arrears(game)
        self.assertEqual((reason["what"], reason["kind"]), ("arrears", "money"))

    def test_a_solvent_household_has_no_arrears(self):
        self.assertIsNone(stuck._stuck_arrears(_game(capital=0.0)))


class ShutConcernAdviceTest(unittest.TestCase):
    def _game(self, refusal, affordable=True):
        return _game(done={"mill"}, is_venture=lambda node_id: True, venture_real_earnings=lambda node_id: 100.0,
                     venture_real_upkeep=lambda node_id: 20.0, open_refusal=lambda node_id, unit_count=None, with_advice=True: refusal,
                     opening_fee=lambda node_id: (30.0 if affordable else 3000.0,), spending_power=lambda purpose: 500.0)

    def test_an_openable_concern_is_advised_with_the_open_command(self):
        reason = stuck._stuck_shut_ventures(self._game(None), {})
        self.assertEqual(reason["what"], "things you built and never opened")
        self.assertIn("'open mill'", reason["why"])

    def test_a_concern_open_would_refuse_for_staff_is_not_advised_and_names_the_cause(self):
        refusal = Refusal("craft_staff", "you need more craftsmen to supervise it.")
        reason = stuck._stuck_shut_ventures(self._game(refusal), {})
        self.assertEqual(reason["what"], "things you built and cannot open yet")
        self.assertEqual((reason["the_best_one"], reason["blocked_by"]), ("mill", "craft_staff"))
        self.assertNotIn("'open mill'", reason["why"])

    def test_a_concern_the_household_cannot_pay_to_open_is_blocked_by_cash(self):
        reason = stuck._stuck_shut_ventures(self._game(None, affordable=False), {})
        self.assertEqual(reason["blocked_by"], "cash_short")
        self.assertNotIn("'open mill'", reason["why"])

    def test_no_shut_profitable_concern_is_no_reason(self):
        game = self._game(None)
        game.operating = {"mill"}
        self.assertIsNone(stuck._stuck_shut_ventures(game, {}))


if __name__ == "__main__":
    unittest.main()
