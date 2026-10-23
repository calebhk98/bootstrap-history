"""Complaint 79: a standing shortage is a row of the `state` reply and the state screen prints it as one block. The rows come
from `condition_rows` on a stand-in game and the block from `_state_conditions` on a built reply (no game). The shortage rules
are test_report_noise."""
import unittest
from types import SimpleNamespace

from sim.engine import shortage_conditions
from sim.ui.proto.render_screen_state_blocks import _state_conditions

QUICK_TOPIC = True


def shortage_game():
    return SimpleNamespace(state=SimpleNamespace(scenario=SimpleNamespace(year=100),
                                                 holdings=SimpleNamespace(shortage_condition=None)),
                           material_shortfall_t=lambda material: 0.0)


class StandingShortageOnTheStateScreen(unittest.TestCase):

    def test_a_noted_shortage_is_a_row_with_its_material_and_throughput(self):
        game = shortage_game()
        shortage_conditions.note_shortage(game, "charcoal", 0.46)
        rows = shortage_conditions.condition_rows(game)
        self.assertEqual([(row["material"], row["throughput"]) for row in rows], [("charcoal", 0.46)])

    def test_the_screen_prints_one_block_per_row(self):
        game = shortage_game()
        shortage_conditions.note_shortage(game, "charcoal", 0.46)
        lines = _state_conditions({"conditions": shortage_conditions.condition_rows(game)})
        self.assertEqual(len([line for line in lines if line]), 1)

    # presentation: the state screen prints the standing condition as a block naming the material and the share
    def test_the_block_names_the_material_and_the_share(self):
        game = shortage_game()
        shortage_conditions.note_shortage(game, "charcoal", 0.46)
        text = "\n".join(_state_conditions({"conditions": shortage_conditions.condition_rows(game)}))
        self.assertIn("CHARCOAL", text.upper())
        self.assertIn("46%", text)

    def test_with_no_shortage_the_screen_prints_nothing(self):
        self.assertEqual(_state_conditions({}), [])
        self.assertEqual(shortage_conditions.condition_rows(shortage_game()), [])


if __name__ == "__main__":
    unittest.main()
