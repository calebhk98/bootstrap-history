"""Complaint 294: `stuck` stops recommending the cheapest start while a savings target stands. `_stuck_started_nothing` called
with and without the saving flag on a stand-in game. The plan and its row are test_saving_target."""
import unittest
from types import SimpleNamespace

from sim.ui.proto.dispatch_inspection_stuck import _stuck_started_nothing

QUICK_TOPIC = True

COSTS = {"cheap": 100.0, "dear": 900.0}


def idle_game():
    return SimpleNamespace(active={}, training=[], project_cost=COSTS.get)


class IdleRow(unittest.TestCase):

    def test_without_a_target_the_row_recommends_the_cheapest_affordable_start(self):
        row = _stuck_started_nothing(idle_game(), ["cheap", "dear"], ["cheap", "dear"])
        self.assertEqual(row["kind"], "idle")
        self.assertIn("cheap", row["why"])
        self.assertNotIn("dear", row["why"])

    def test_the_cheapest_is_chosen_among_what_can_be_afforded_before_what_can_only_be_started(self):
        row = _stuck_started_nothing(idle_game(), ["cheap", "dear"], ["dear"])
        self.assertIn("dear", row["why"])

    def test_while_saving_the_row_is_still_idle_but_names_no_start(self):
        row = _stuck_started_nothing(idle_game(), ["cheap", "dear"], ["cheap", "dear"], saving=True)
        self.assertEqual(row["kind"], "idle")
        self.assertNotIn("cheap", str(row))
        self.assertNotIn("dear", str(row))

    def test_work_in_hand_makes_no_row_whatever_the_saving_flag(self):
        busy = SimpleNamespace(active={"p": {}}, training=[], project_cost=COSTS.get)
        self.assertIsNone(_stuck_started_nothing(busy, ["cheap"], ["cheap"]))
        self.assertIsNone(_stuck_started_nothing(busy, ["cheap"], ["cheap"], saving=True))


if __name__ == "__main__":
    unittest.main()
