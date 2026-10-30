"""The `state` command marks the shut-concerns pointer as seen once it has been shown, and `full` shows it again. `_cmd_state` is
called with its reply builder replaced by a recorder and a stand-in game; the once-only rule is test_state_repetition."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest
from unittest import mock

from sim.ui.proto import dispatch_inspection
from sim.tests.ui_stand_in import Game

SHUT = "you_know_how_to_run_but_have_not_opened"
SEEN = "shut_concerns_pointer_seen"


def ask(game, reply, **command):
    with mock.patch.object(dispatch_inspection, "_agent_state", lambda sim, nodes, cmd: dict(reply)):
        return dispatch_inspection._cmd_state(game, {}, command, False)


def stand_in_game():
    return Game(year=100, state=Game(acting_record=Game(seat_progress=Game(_said_explanations=None))))


class StateExplainsShutConcernsOnce(unittest.TestCase):
    def test_the_first_state_carries_no_seen_mark_and_a_later_one_does(self):
        game = stand_in_game()
        first = ask(game, {SHUT: 5})
        second = ask(game, {SHUT: 5})
        self.assertNotIn(SEEN, first)
        self.assertIs(second[SEEN], True)

    def test_full_explains_it_again(self):
        game = stand_in_game()
        ask(game, {SHUT: 5})
        self.assertNotIn(SEEN, ask(game, {SHUT: 5}, full=True))

    def test_a_state_with_no_shut_concerns_marks_nothing_and_does_not_use_up_the_explanation(self):
        game = stand_in_game()
        ask(game, {})
        ask(game, {})
        self.assertNotIn(SEEN, ask(game, {SHUT: 5}))


if __name__ == "__main__":
    unittest.main()
