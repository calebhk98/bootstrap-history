"""The per-year step hook (`step_progress`) and the demographic emergency block, each called on inputs written out here."""

QUICK_TOPIC = True

import io
import types
import unittest
from unittest import mock

from sim.ui import cli_interactive
from sim.ui.proto import step_progress
from sim.ui.proto.step_alerts import DEMOGRAPHIC_EMERGENCY_DROP, demographic_emergency

SUMMARY = {"year": 101, "capital": 5.0, "completed": 2, "closed": 1, "population_change": -0.02}


class AfterYearHook(unittest.TestCase):
    def tearDown(self):
        step_progress.set_after_year(None)

    def test_after_year_calls_the_callback_with_the_sim_and_summary(self):
        calls = []
        step_progress.set_after_year(lambda sim, summary: calls.append((sim, summary)))
        step_progress.after_year("a sim", SUMMARY)
        self.assertEqual(calls, [("a sim", SUMMARY)])

    def test_after_year_with_no_callback_does_nothing(self):
        step_progress.set_after_year(None)
        self.assertIsNone(step_progress.after_year("a sim", SUMMARY))


class CommitAndReport(unittest.TestCase):
    def commit(self, summary, session="game.json", seconds_since_save=0.0):
        stream = io.StringIO()
        saved = []
        with mock.patch("sim.engine.ui_port.money_text", return_value="MONEY"), \
                mock.patch("sim.ui.memory.save_session", lambda sim, path: saved.append(path)), \
                mock.patch.object(step_progress.time, "monotonic", side_effect=[0.0, seconds_since_save, seconds_since_save]):
            step_progress.commit_and_report(session, stream)("a sim", summary)
        return stream.getvalue(), saved

    def test_a_multi_year_step_writes_one_line_per_year(self):
        text, _ = self.commit({**SUMMARY, "years_asked": 3})
        self.assertEqual(text.count("\n"), 1)
        self.assertIn("year 101", text)

    def test_a_one_year_step_writes_nothing_and_saves_nothing(self):
        text, saved = self.commit({**SUMMARY, "years_asked": 1}, seconds_since_save=1e6)
        self.assertEqual((text, saved), ("", []))

    def test_it_saves_once_the_interval_has_passed(self):
        _, saved = self.commit({**SUMMARY, "years_asked": 3}, seconds_since_save=step_progress.SAVE_INTERVAL_SECONDS)
        self.assertEqual(saved, ["game.json"])

    def test_it_does_not_save_before_the_interval(self):
        _, saved = self.commit({**SUMMARY, "years_asked": 3}, seconds_since_save=step_progress.SAVE_INTERVAL_SECONDS / 2)
        self.assertEqual(saved, [])

    def test_the_last_asked_year_is_left_for_the_caller_to_save(self):
        _, saved = self.commit({**SUMMARY, "years_asked": 3, "last_asked_year": True}, seconds_since_save=1e6)
        self.assertEqual(saved, [])


class PlayedCommandClearsTheHook(unittest.TestCase):
    def test_the_hook_is_cleared_once_the_command_is_done(self):
        policy = types.SimpleNamespace(after_command=lambda sim, cmd, ended: None)
        seen_during = []

        def dispatch(sim, nodes, cmd):
            seen_during.append(step_progress._after_year[0])
            return {"ok": True}
        with mock.patch.object(cli_interactive, "_agent_dispatch", dispatch), \
                mock.patch.object(cli_interactive, "_agent_end_reason", lambda sim: None), \
                mock.patch.object(cli_interactive, "render_pretty", lambda name, reply: ""), \
                mock.patch("builtins.print"):
            cli_interactive._play_run_one_command("a sim", {}, {"cmd": "state"}, "game.json", policy)
        self.assertIsNotNone(seen_during[0])
        self.assertIsNone(step_progress._after_year[0])


class DemographicEmergency(unittest.TestCase):
    def test_a_drop_past_the_threshold_is_an_emergency_carrying_the_change(self):
        change = -DEMOGRAPHIC_EMERGENCY_DROP - 0.1
        self.assertEqual(demographic_emergency(change), {"population_change": change})

    def test_a_small_change_or_none_is_no_emergency(self):
        self.assertIsNone(demographic_emergency(0.0))
        self.assertIsNone(demographic_emergency(None))


if __name__ == "__main__":
    unittest.main()
