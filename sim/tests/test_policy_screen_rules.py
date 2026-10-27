"""The `policy` screen says the automatic behaviours are approximations and says what every switch the game offers does
(`dispatch_ventures._cmd_policy`). Called on a stand-in game holding the default policy."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.engine.seat_defaults import default_policy
from sim.ui.proto.dispatch_ventures import _cmd_policy


def _reply(manual):
    household = types.SimpleNamespace(reserve_craftsmen=0, reserve_scholars=0)
    game = types.SimpleNamespace(policy=default_policy(manual), capital=1000.0, year=100, credit_frozen_until=0,
                                 workforce=household, view=workforce_stand_in.view_of(household, exclusions=set, keep_staffed=set), state=types.SimpleNamespace(household=household, projects=types.SimpleNamespace(excluded=set())))
    return _cmd_policy(game, {}, {"cmd": "policy"}, None)


class PolicyScreenTest(unittest.TestCase):
    def test_the_screen_says_these_are_approximations(self):
        for manual in (True, False):
            self.assertTrue(_reply(manual).get("these_are_approximations_not_optimal_play"))

    def test_every_switch_the_game_offers_says_what_it_does(self):
        for manual in (True, False):
            reply = _reply(manual)
            undescribed = [name for name in reply["policy"] if not (reply.get("what_each_does") or {}).get(name)]
            self.assertEqual(undescribed, [], manual)


if __name__ == "__main__":
    unittest.main()
