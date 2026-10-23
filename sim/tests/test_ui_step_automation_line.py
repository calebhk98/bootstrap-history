"""The step screen says what automation and the standing programme did (Complaints 91, 74). Complaint 640: the line, the
screen and the audit window are called on rows built here; which rows the step reply carries is
test_step_automation_rows."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine import automation_audit
from sim.ui.proto.render_screen_step import render_step
from sim.ui.proto.step_automation import automation_lines

ROWS = [{"year": 101, "policy": "auto_hire", "action": "hire", "what": "2 smiths", "reason": "short", "cost": 120},
        {"year": 101, "policy": "auto_hire", "action": "hire", "what": "1 scribe", "reason": "short", "cost": 80},
        {"year": 101, "policy": "auto_open", "action": "reopen", "what": "a mill", "reason": "staffed", "cost": 0}]


class AutomationLineTests(unittest.TestCase):

    def test_automation_is_one_line_counting_each_policys_actions_with_their_capital(self):
        line = automation_lines(ROWS)
        self.assertEqual(len(line), 1)
        # presentation: the line reads "<policy> <action> xN, capital"
        self.assertIn("auto_hire hire x2, 200", line[0])
        self.assertIn("auto_open reopen x1", line[0])

    def test_no_automation_rows_means_no_line(self):
        self.assertEqual(automation_lines([]), [])

    def test_the_step_screen_shows_the_automation_line_and_the_programme_block(self):
        screen = render_step({"ok": True, "completed": [], "events": [], "automation": ROWS,
                              "programme": [{"year": 101, "what": "goal route", "started": [], "skipped": [],
                                             "spent": 0.0, "did_nothing_because": "paused"}]})
        # presentation: the screen's section headings
        for word in ("AUTOMATION:", "PROGRAMME:", "paused"):
            self.assertIn(word, screen)

    def test_the_pointer_to_the_full_state_is_the_last_line_exactly_once(self):
        from sim.ui.proto.render_screen_step import FULL_STATE_POINTER
        text = render_step({"ok": True, "completed": [], "events": []})
        self.assertEqual(text.count(FULL_STATE_POINTER), 1)
        self.assertEqual(text.splitlines()[-1], FULL_STATE_POINTER)


class AuditWindowTests(unittest.TestCase):

    def _game(self, year):
        household = types.SimpleNamespace(automation_audit=[{"year": 99, "what": "old"}, {"year": 100, "what": "last"},
                                                            {"year": 101, "what": "now"}])
        return types.SimpleNamespace(state=types.SimpleNamespace(
            scenario=types.SimpleNamespace(year=year), household=household))

    def test_the_rows_are_those_of_the_years_just_played_oldest_first(self):
        game = self._game(102)
        self.assertEqual([row["what"] for row in automation_audit.rows(game, 1)], ["now"])
        self.assertEqual([row["what"] for row in automation_audit.rows(game, 3)], ["old", "last", "now"])


if __name__ == "__main__":
    unittest.main()
