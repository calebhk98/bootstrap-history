"""Complaint 161: the risk shown is the risk rolled. `risk_rules.attempt_fails` is the roll: a draw just under the risk
fails and one just over does not. The projects module's `_complete` takes the risk from `effective_risk`, the function `why`
quotes, on a first attempt and a later one, and makes one draw per attempt."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.projects.risk_rules import attempt_fails
from sim.tests import projects_host

NODE_ID = "kiln"


class RecordingRandom:
    def __init__(self, draw):
        self.draw = draw
        self.draws = 0

    def random(self):
        self.draws += 1
        return self.draw


def RollSim(draw, risk_by_attempt):
    """A project whose roll fails: the module records the risk `_fail_attempt` is given."""
    module = projects_host.build(tree={NODE_ID: {}}, game_random=RecordingRandom(draw))
    module.dice = module.needs.game_random()
    module.rolled_against = []
    module.effective_risk = lambda node_id, precaution=None: risk_by_attempt[module.seat.failed_attempts[node_id]]
    module._fail_attempt = lambda node_id, risk_this_attempt: module.rolled_against.append(risk_this_attempt)
    return module


class RollTests(unittest.TestCase):
    def test_a_draw_just_under_the_risk_fails(self):
        self.assertTrue(attempt_fails(0.3 - 1e-9, 0.3))

    def test_a_draw_just_over_the_risk_succeeds(self):
        self.assertFalse(attempt_fails(0.3 + 1e-9, 0.3))

    def test_a_risk_of_nothing_never_fails_and_a_draw_of_nothing_fails_any_risk(self):
        self.assertFalse(attempt_fails(0.0, 0.0))
        self.assertTrue(attempt_fails(0.0, 1e-12))


class CompleteRollsTheShownRiskTests(unittest.TestCase):
    RISKS = {0: 0.40, 2: 0.25}

    def complete_failing(self, failed_attempts):
        game = RollSim(draw=0.0, risk_by_attempt=self.RISKS)
        game.seat.failed_attempts[NODE_ID] = failed_attempts
        game._complete(NODE_ID)
        return game

    def test_the_risk_the_attempt_is_rolled_against_is_the_one_effective_risk_quotes(self):
        for failed_attempts, shown in self.RISKS.items():
            game = self.complete_failing(failed_attempts)
            self.assertEqual(game.rolled_against, [shown])

    def test_the_roll_is_a_single_draw_per_attempt(self):
        self.assertEqual(self.complete_failing(0).dice.draws, 1)


if __name__ == "__main__":
    unittest.main()
