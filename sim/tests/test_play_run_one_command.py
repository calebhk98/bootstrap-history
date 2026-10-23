"""The play loop's single command (ui/cli_interactive._play_run_one_command): the command is dispatched, then the save
policy is asked once (before anything is printed), whether the dispatch answered, failed, or the reader hung up.
When a save is written is test_complaint_181_save_cost (the unchanged game) and ui/save_policy.py."""
QUICK_TOPIC = True

import contextlib
import io
import types
import unittest
from unittest import mock

from sim.ui import cli_interactive


class _Policy:
    def __init__(self):
        self.calls = []

    def after_command(self, sim, cmd, ended=False):
        self.calls.append((sim, cmd, ended))


class RunOneCommandTests(unittest.TestCase):
    def setUp(self):
        self.order = []
        self.policy = _Policy()
        self.sim = object()
        self.rendered = []
        self.end_reason = None

    def run_command(self, cmd, dispatch=None, render=None):
        def default_dispatch(sim, nodes, command):
            self.order.append("dispatch")
            return {"ok": True}

        def default_render(name, reply):
            self.order.append("render")
            self.rendered.append(reply)
            return "text"

        self.policy.after_command = lambda sim, command, ended=False: (
            self.order.append("save"), self.policy.calls.append((sim, command, ended)))
        progress = types.SimpleNamespace(set_after_year=lambda value: None, commit_and_report=lambda session, stream: None)
        with mock.patch.object(cli_interactive, "_agent_dispatch", dispatch or default_dispatch), \
                mock.patch.object(cli_interactive, "render_pretty", render or default_render), \
                mock.patch.object(cli_interactive, "_agent_end_reason", lambda game: self.end_reason), \
                mock.patch.object(cli_interactive, "step_progress", progress), \
                contextlib.redirect_stdout(io.StringIO()):
            return cli_interactive._play_run_one_command(self.sim, {}, cmd, "session.json", self.policy)

    def test_the_policy_is_asked_once_with_the_game_and_the_command(self):
        cmd = {"cmd": "state"}
        self.assertFalse(self.run_command(cmd))
        self.assertEqual(self.policy.calls, [(self.sim, cmd, False)])

    def test_the_save_comes_after_the_dispatch_and_before_the_printing(self):
        self.run_command({"cmd": "state"})
        self.assertEqual(self.order, ["dispatch", "save", "render"])

    def test_a_game_that_has_ended_tells_the_policy_so(self):
        self.end_reason = "horizon reached"
        self.run_command({"cmd": "state"})
        self.assertTrue(self.policy.calls[0][2])

    def test_a_dispatch_that_fails_answers_not_ok_and_is_still_saved(self):
        def failing(sim, nodes, command):
            raise KeyError("boom")

        self.run_command({"cmd": "state"}, dispatch=failing)
        self.assertEqual(len(self.policy.calls), 1)
        self.assertIs(self.rendered[0]["ok"], False)

    def test_a_reader_that_hung_up_ends_the_loop_after_the_save(self):
        def hung_up(name, reply):
            raise BrokenPipeError()

        self.assertTrue(self.run_command({"cmd": "state"}, render=hung_up))
        self.assertEqual(len(self.policy.calls), 1)


if __name__ == "__main__":
    unittest.main()
