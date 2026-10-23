"""Complaints 145 and 154: `why` prints the specialist foreman `open` will demand, and its serial floor counts only what
is still unbuilt. Complaint 640: the floor is `remaining_critical_path_years` on the real tree and the screen text is
rendered from replies built here; the reply's foreman field is test_offers_unit_price_and_foreman_reply."""
QUICK_TOPIC = True

import unittest

from .harness import NODES
from sim.engine.critical_path_remaining import remaining_critical_path_years
from sim.engine.data import closure, critical_path
from sim.ui.proto.render_screen_why import _why_chain, _why_staff_keep_open

GOAL = "point_contact_transistor"


class RemainingFloorTests(unittest.TestCase):

    def test_with_nothing_built_the_remaining_floor_equals_the_from_scratch_floor(self):
        whole = critical_path(NODES, GOAL)[0]
        self.assertAlmostEqual(remaining_critical_path_years(NODES, GOAL, set()), whole, places=9)

    def test_with_every_prerequisite_built_only_the_goals_own_time_remains(self):
        whole = critical_path(NODES, GOAL)[0]
        own = remaining_critical_path_years(NODES, GOAL, set(NODES) - {GOAL})
        self.assertTrue(0 < own < whole, (own, whole))

    def test_a_finished_goal_has_no_floor_left(self):
        self.assertEqual(remaining_critical_path_years(NODES, GOAL, set(NODES)), 0.0)

    def test_an_active_node_counts_its_remaining_time_not_its_floor(self):
        self.assertEqual(remaining_critical_path_years(NODES, GOAL, set(NODES) - {GOAL}, {GOAL: 0.25}), 0.25)

    def test_the_floor_left_shrinks_once_the_chain_is_built_and_the_from_scratch_floor_does_not(self):
        whole = critical_path(NODES, GOAL)[0]
        built = closure(NODES, GOAL) - {GOAL}
        self.assertLess(remaining_critical_path_years(NODES, GOAL, built),
                        remaining_critical_path_years(NODES, GOAL, set()))
        self.assertEqual(critical_path(NODES, GOAL)[0], whole)


class WhyScreenTests(unittest.TestCase):

    def test_the_screen_shows_the_specialist_foreman_trade_and_fte_of_the_reply(self):
        reply = {"staff_to_keep_it_open": {"scholars": 1, "artisans": 2},
                 "specialist_foreman_to_keep_it_open": {"trade": "smith", "fte": 0.5, "free_now": 3}}
        text = "\n".join(_why_staff_keep_open(reply))
        # presentation: the foreman line is screen text, here asserted by trade, figure and unit
        self.assertIn("smith", text)
        self.assertIn("FTE", text)
        self.assertIn("0.5", text)

    def test_no_foreman_line_when_the_reply_names_none(self):
        reply = {"staff_to_keep_it_open": {"scholars": 1, "artisans": 2}}
        self.assertNotIn("FOREMAN", "\n".join(_why_staff_keep_open(reply)))

    def test_the_screen_labels_the_floor_left_and_the_from_scratch_floor(self):
        reply = {"chain_size": 5, "critical_path_years_remaining": 12.0, "critical_path_years": 30.0}
        text = "\n".join(_why_chain(reply))
        # presentation: both figures and their labels are what a player reads
        self.assertIn("serial floor left", text)
        self.assertIn("from scratch", text)
        self.assertIn("12", text)
        self.assertIn("30", text)

    def test_with_no_remaining_figure_the_from_scratch_floor_is_the_floor_left(self):
        reply = {"chain_size": 5, "critical_path_years": 30.0}
        self.assertIn("30-year serial floor left", "\n".join(_why_chain(reply)))   # presentation: the line's wording


if __name__ == "__main__":
    unittest.main()
