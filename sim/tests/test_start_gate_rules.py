"""Start gates: a built-then-shut work reads as `mothballed` (not as new research or as done), `restore` refuses what was not shut or is no
longer known and says to build it again, and `ignore_trade` skips only the trade-exists check, not the staff gate. Each check is
called on a stand-in game carrying what it reads."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import projects_starting
from sim.engine.blockers import classify_plain_check
from sim.engine.projects_staffing import StaffingMixin
from sim.engine.projects_starting import StartingMixin

WORK = "md2_sand_filtration"


def _game(done=(), mothballed=(), absent_trades=(), craft_short=False):
    projects = types.SimpleNamespace(done=set(done), mothballed=set(mothballed))
    labour = types.SimpleNamespace(trade_available=lambda trade: trade not in absent_trades,
                                   craft_hands_available=lambda: 0.0 if craft_short else 5.0,
                                   staff_advice=lambda kind, deficit: "hire", market_supply=lambda trade: 1.0)
    return types.SimpleNamespace(state=types.SimpleNamespace(projects=projects, household=types.SimpleNamespace(),
                                                         scenario=types.SimpleNamespace(year=100)), labour=labour,
                                 reopen_fee=lambda node_id, units: 40.0, reopen_units=lambda node_id: 1.0, civ={})


class AlreadyDoneCheckTest(unittest.TestCase):
    def test_a_mothballed_work_is_refused_as_something_to_restore_not_as_new_research(self):
        verdict = StartingMixin._check_already_done(_game(done={WORK}, mothballed={WORK}), WORK, {}, False, None, True)
        self.assertIs(verdict[0], False)
        self.assertIn('"cmd":"restore"', verdict[1])   # presentation: the refusal carries the command that reopens it

    def test_a_work_that_is_done_and_running_is_refused_as_done(self):
        self.assertEqual(StartingMixin._check_already_done(_game(done={WORK}), WORK, {}, False, None, True), (False, "already done"))

    def test_a_work_not_built_has_no_opinion_here(self):
        self.assertIsNone(StartingMixin._check_already_done(_game(), WORK, {}, False, None, True))

    def test_the_refusal_without_a_message_is_the_same_verdict(self):
        game = _game(done={WORK}, mothballed={WORK})
        self.assertEqual(StartingMixin._check_already_done(game, WORK, {}, False, None, False), (False, None))


class MothballedCauseTest(unittest.TestCase):
    def test_a_done_work_that_is_mothballed_reports_the_cause_mothballed_and_a_closed_kind(self):
        entry = classify_plain_check("_check_already_done", "done", "text", [], None, True)
        self.assertEqual((entry["kind"], entry["cause"]), ("closed", "mothballed"))

    def test_a_done_work_that_is_not_mothballed_reports_already_done(self):
        entry = classify_plain_check("_check_already_done", "done", "text", [], None, False)
        self.assertEqual((entry["kind"], entry["cause"]), ("done", "already_done"))


class RestoreRefusalsTest(unittest.TestCase):
    def test_a_work_that_was_not_shut_cannot_be_restored(self):
        ok, _message = StaffingMixin.restore_work(_game(done={WORK}), WORK)
        self.assertFalse(ok)

    def test_a_work_whose_knowledge_is_gone_cannot_be_restored_and_the_start_command_is_named(self):
        ok, message = StaffingMixin.restore_work(_game(mothballed={WORK}), WORK)
        self.assertFalse(ok)
        self.assertIn('"cmd":"start"', message)   # presentation: the refusal carries the command that builds it again


class IgnoreTradeTest(unittest.TestCase):
    NODE = {"lab": {"optician": 100.0}}

    def test_a_missing_trade_refuses_the_start_unless_the_trade_check_is_skipped(self):
        game = _game(absent_trades={"optician"})
        with mock.patch.object(projects_starting, "training_advice", lambda labour, trade: {}), \
                mock.patch.object(projects_starting, "training_advice_text", lambda advice: "teach one"):
            refused = StartingMixin._check_absent_trades(game, "node", self.NODE, False, None, True)
        self.assertIs(refused[0], False)
        self.assertIsNone(StartingMixin._check_absent_trades(game, "node", self.NODE, True, None, True))

    def test_skipping_the_trade_check_does_not_skip_the_staff_gate(self):
        game = _game(craft_short=True)
        with mock.patch.object(projects_starting.research_gate, "hands_short", lambda need, have: need - have):
            verdict = StartingMixin._check_craft_staff(game, "node", {"art": 2.0}, True, None, False)
        self.assertEqual(verdict, (False, None))


if __name__ == "__main__":
    unittest.main()
