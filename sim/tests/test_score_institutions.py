"""The score's institutions component (ui/proto/score_institutions.py), on a stand-in game: scalable institutions count
by units against their ceiling, the others by running, and the figure does not move with the order the institutions are
held in (the sum runs over floats)."""
QUICK_TOPIC = True

import itertools
import types
import unittest

from sim.ui.proto.score_institutions import institutions_component

UNITS = {"workshop": 1.0, "school": 1.0, "academy": 2.0}
CEILINGS = {"workshop": 3.0, "school": 7.0, "academy": 0.0}
RUNNING = {"press", "granary"}
FINISHED = {"press", "granary", "library"}


def game(institutions):
    return types.SimpleNamespace(
        CAPABILITY_INSTITUTIONS=institutions, SCALABLE_INSTITUTIONS={"workshop", "school", "academy"},
        institution_units=lambda institution_id: UNITS[institution_id],
        institution_unit_ceiling=lambda institution_id: CEILINGS[institution_id],
        running=lambda institution_id: institution_id in RUNNING, has=lambda institution_id: institution_id in FINISHED)


NAMES = ["workshop", "school", "academy", "press", "granary", "library"]


class InstitutionsComponentTests(unittest.TestCase):
    def test_scalable_ones_count_by_units_over_ceiling_the_rest_by_running(self):
        component = institutions_component(game(NAMES))
        expected = (1.0 / 3.0 + 1.0 / 7.0 + 1.0 + 1.0 + 1.0 + 0.0) / 6.0
        self.assertAlmostEqual(component["normalized"], expected, places=15)

    def test_a_ceiling_below_one_is_taken_as_one(self):
        self.assertEqual(institutions_component(game(["academy"]))["normalized"], 1.0)

    def test_the_counted_and_the_finished_but_shut_are_named(self):
        component = institutions_component(game(NAMES))
        self.assertEqual(component["counted"], ["academy", "granary", "press", "school", "workshop"])
        self.assertEqual(component["finished_but_closed"], ["library"])
        self.assertEqual((component["raw"], component["of_total"]), (5, 6))

    def test_no_institutions_scores_nothing(self):
        self.assertEqual(institutions_component(game([]))["normalized"], 0.0)

    def test_every_order_the_institutions_are_held_in_gives_the_identical_figure(self):
        figures = {institutions_component(game(list(order)))["normalized"] for order in itertools.permutations(NAMES)}
        self.assertEqual(len(figures), 1)


if __name__ == "__main__":
    unittest.main()
