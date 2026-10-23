"""Complaint 79: a standing shortage is a row of the `state` reply (`condition_rows`) and the state screen prints rows as one
block (`_state_conditions`). Each called once on a stand-in or reply written out here. The shortage rules are test_report_noise."""
import unittest
from types import SimpleNamespace

from sim.engine import shortage_conditions
from sim.ui.proto.render_screen_state_blocks import _state_conditions

QUICK_TOPIC = True

ROW = {"material": "charcoal", "throughput": 0.46, "years": 1, "trend": "steady"}


def game(condition, shortfall=0.0):
    return SimpleNamespace(state=SimpleNamespace(scenario=SimpleNamespace(year=100), holdings=SimpleNamespace(shortage_condition=condition)),
                           material_shortfall_t=lambda material: shortfall)


class ConditionRows(unittest.TestCase):

    def test_a_standing_shortage_is_one_row_with_its_material_throughput_and_years(self):
        rows = shortage_conditions.condition_rows(
            game({"material": "charcoal", "since": 100, "reported": 0.46, "previous": 0.46, "latest": 0.46}))
        self.assertEqual([(row["material"], row["throughput"], row["years"]) for row in rows], [("charcoal", 0.46, 1)])

    def test_no_shortage_gives_no_rows(self):
        self.assertEqual(shortage_conditions.condition_rows(game(None)), [])

    def test_a_deficit_is_added_to_the_row(self):
        rows = shortage_conditions.condition_rows(
            game({"material": "charcoal", "since": 100, "reported": 0.5, "previous": 0.5, "latest": 0.5}, shortfall=12.34))
        self.assertEqual(rows[0]["deficit_tonnes_per_year"], 12.3)


class ConditionsBlock(unittest.TestCase):

    def test_one_row_prints_one_line_after_a_blank(self):
        lines = _state_conditions({"conditions": [ROW]})
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "")

    # presentation: the state screen prints the standing condition as a block naming the material and the share
    def test_the_block_names_the_material_and_the_share(self):
        text = "\n".join(_state_conditions({"conditions": [ROW]}))
        self.assertIn("CHARCOAL", text.upper())
        self.assertIn("46%", text)

    def test_no_rows_print_nothing(self):
        self.assertEqual(_state_conditions({}), [])


if __name__ == "__main__":
    unittest.main()
