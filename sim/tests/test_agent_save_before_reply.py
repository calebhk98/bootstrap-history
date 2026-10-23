"""The agent loop saves the session before it writes the reply, so a closed pipe costs the reply and never the state change that
produced it (`cli_agent._agent_loop`), and a `start` short of cash carries the borrowing forecast built from the game's own cash,
credit line and rate (`credit_forecast.start_credit_forecast`). Called on stand-ins for the dispatcher, the save policy and the
game; no process is spawned and no game is built."""
import io
import types
import unittest
from unittest import mock

from sim.ui import cli_agent
from sim.ui.proto import credit_forecast

QUICK_TOPIC = True


class Policy:
    session = None

    def __init__(self, events):
        self.events = events

    def after_command(self, sim, command, ended):
        self.events.append(("saved", command["cmd"]))


def run_loop(lines, emit):
    events = []
    args = types.SimpleNamespace(script=None)
    dispatch = lambda sim, nodes, command: events.append(("ran", command["cmd"])) or {"ok": True}
    with mock.patch.object(cli_agent, "_agent_dispatch", dispatch), \
            mock.patch.object(cli_agent, "_agent_end_reason", lambda sim: None), \
            mock.patch.object(cli_agent.sys, "stdin", io.StringIO(lines)), \
            mock.patch.object(cli_agent.sys, "stdout", io.StringIO()):
        result = cli_agent._agent_loop(object(), {}, args, lambda reply, name=None: emit(events, reply), Policy(events))
    return result, events


class SaveBeforeReplyTests(unittest.TestCase):
    def test_each_command_is_saved_before_its_reply_is_written(self):
        result, events = run_loop('{"cmd": "step"}\n{"cmd": "state"}\n', lambda events, reply: events.append(("replied", reply)))
        self.assertEqual(result, 0)
        self.assertEqual([event[0] for event in events], ["ran", "saved", "replied", "ran", "saved", "replied"])

    def test_a_closed_pipe_costs_the_reply_not_the_commands_progress(self):
        def closed(events, reply):
            raise BrokenPipeError()
        result, events = run_loop('{"cmd": "step"}\n{"cmd": "state"}\n', closed)
        self.assertEqual(result, 0)
        self.assertEqual(events, [("ran", "step"), ("saved", "step")])


class StartCreditForecastTests(unittest.TestCase):
    def sim(self, capital):
        return types.SimpleNamespace(capital=capital, credit_limit=lambda: 5000.0, debt_interest_rate=lambda: 0.08,
                                     debt_service_forecast=lambda owed: {"interest_per_year_at_that_draw": owed * 0.08})

    def test_a_start_short_of_cash_reports_the_gap_from_the_games_cash_limit_and_rate(self):
        forecast = credit_forecast.start_credit_forecast(self.sim(400.0), 1000.0, 100.0)
        self.assertEqual(forecast["you_would_borrow"], 600.0)
        self.assertEqual(forecast["interest_rate_percent"], 8.0)
        self.assertEqual(forecast["no_one_advances_past"], 5000.0)
        self.assertEqual(forecast["interest_per_year_at_that_draw"], 48.0)

    def test_a_start_paid_outright_reports_no_borrowing(self):
        self.assertIsNone(credit_forecast.start_credit_forecast(self.sim(20000.0), 1000.0, 100.0))


if __name__ == "__main__":
    unittest.main()
