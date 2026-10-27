"""`available` marks a project short of staff exactly when the start gate would refuse it for staff: the founder's own hands and
what is under contract count (`techtree._short_of_staff`). Called on a stand-in labour."""
QUICK_TOPIC = True

import types
import unittest

from sim.ui.proto.techtree import _short_of_staff
from sim.tests.ui_stand_in import Game


def _game(craft_hands, scholars):
    labour = Game(craft_hands_available=lambda: craft_hands, effective_scholars=lambda: scholars)
    return Game(labour=labour)


class ShortOfStaffTest(unittest.TestCase):
    def test_a_job_the_hands_on_hand_can_do_is_not_marked(self):
        self.assertFalse(_short_of_staff(_game(1.0, 1.0), {"art": 1.0, "sch": 1.0}))
        self.assertFalse(_short_of_staff(_game(1.0, 1.0), {"art": 0.0, "sch": 0.0}))

    def test_too_many_craftsmen_or_too_many_scholars_marks_it(self):
        self.assertTrue(_short_of_staff(_game(1.0, 1.0), {"art": 20.0, "sch": 0.0}))
        self.assertTrue(_short_of_staff(_game(1.0, 1.0), {"art": 0.0, "sch": 2.0}))


if __name__ == "__main__":
    unittest.main()
