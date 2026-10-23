"""The Endless horizon: a game whose end year comes from ENDLESS_HORIZON_YEARS is still running where a standard horizon
has ended the run, and the `--horizon` flag of run, compare, play and agent keeps the standard default. Rules:
`_agent_end_reason` on a stand-in game (`score_game.ScoreGame`) and the parsed arguments of `cli.main`. The wizard's Endless choice and the sidecar
that keeps the horizon are in test_session_checkpoint_rules."""
QUICK_TOPIC = True

import sys
import unittest

from sim.tests.harness import GOAL, NODES
from sim.tests.score_game import ScoreGame
from sim.ui import cli
from sim.ui.proto.state_waiting import _agent_end_reason

STANDARD_HORIZON_YEARS = 500
YEARS_PLAYED = 600


def game_at_end_year(horizon_years):
	game = ScoreGame(NODES, goal=GOAL)
	game.year = game.cfg["start_year"] + YEARS_PLAYED
	game.end_year = game.cfg["start_year"] + horizon_years
	return game


class EndlessHorizonTests(unittest.TestCase):
	def test_an_endless_game_is_still_running_where_the_standard_horizon_has_ended_the_run(self):
		self.assertIsNone(_agent_end_reason(game_at_end_year(cli.ENDLESS_HORIZON_YEARS)))
		self.assertIsNotNone(_agent_end_reason(game_at_end_year(STANDARD_HORIZON_YEARS)))

	def test_the_horizon_flag_of_every_command_defaults_to_the_standard_horizon(self):
		seen = {}
		names = ("cmd_run", "cmd_compare", "cmd_play", "cmd_agent")
		originals = {name: getattr(cli, name) for name in names}

		def capture(which):
			def handler(args):
				seen[which] = getattr(args, "horizon", None)
				return 0
			return handler

		original_argv = sys.argv
		try:
			for name in names:
				setattr(cli, name, capture(name))
			for command_name in ("run", "compare", "play", "agent"):
				sys.argv = ["simulator.py", command_name]
				cli.main()
		finally:
			sys.argv = original_argv
			for name, handler in originals.items():
				setattr(cli, name, handler)
		self.assertEqual(len(seen), 4)
		self.assertEqual(set(seen.values()), {STANDARD_HORIZON_YEARS})


if __name__ == "__main__":
	unittest.main()
