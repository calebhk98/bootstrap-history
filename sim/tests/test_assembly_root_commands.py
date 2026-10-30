"""The assembly's own module applies the root's operations (`AddSeat`, `MoveSeat`, `RepriceTree`) through the hooks the game sets on the
assembly, and answers what the hook answers; with no game's hook set, asking is an error. Each test calls one handler."""

QUICK_TOPIC = True

import types
import unittest

from sim.assembly.api import AddSeat, AssemblyError, MoveSeat, RepriceTree
from sim.assembly.assemble import _no_root_operation
from sim.assembly.framework import Framework


def framework_over(**hooks):
    framework = Framework()
    framework.assembly = types.SimpleNamespace(**hooks)
    return framework


class RootCommands(unittest.TestCase):
    def test_adding_a_seat_asks_the_games_hook_with_the_id_and_template_and_answers_its_answer(self):
        asked = []
        framework = framework_over(add_seat=lambda seat_id, template: asked.append((seat_id, template)) or "refused")
        self.assertEqual(framework.apply_add_seat(AddSeat("second", {"capital": 5.0})), "refused")
        self.assertEqual(asked, [("second", {"capital": 5.0})])

    def test_moving_a_seat_asks_the_games_hook_and_answers_what_moved(self):
        framework = framework_over(move_seat=lambda from_id, to_id: {"from": from_id, "to": to_id})
        self.assertEqual(framework.apply_move_seat(MoveSeat("a", "b")), {"from": "a", "to": "b"})

    def test_repricing_the_tree_asks_the_games_hook(self):
        asked = []
        framework_over(reprice_tree=lambda: asked.append("tree")).apply_reprice_tree(RepriceTree())
        self.assertEqual(asked, ["tree"])

    def test_a_root_operation_no_game_has_set_is_an_error_naming_it(self):
        with self.assertRaises(AssemblyError) as raised:
            _no_root_operation("add_seat")("second", {})
        self.assertIn("add_seat", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
