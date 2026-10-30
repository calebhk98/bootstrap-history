"""The projects module's `opening_shortfall` hands the concern's hands needed and today's free staff to `staff_shortfall`. Called
on the module over two staff readers written out."""

QUICK_TOPIC = True

import unittest

from sim.tests import projects_host


def game(need, free):
    asked = []

    def venture_hands(node_id):
        asked.append(node_id)
        return need
    module = projects_host.build(venture_hands=venture_hands, venture_staff_free=lambda: free)
    module.asked = asked
    return module


class OpeningShortfall(unittest.TestCase):
    def test_free_staff_below_the_need_gives_need_and_free_for_that_concern(self):
        stand_in = game(need=(5.0, 5.0), free=(0.0, 0.0))
        self.assertEqual(stand_in.opening_shortfall("school_founded"), (5.0, 5.0, 0.0, 0.0))
        self.assertEqual(stand_in.asked, ["school_founded"])

    def test_free_staff_covering_the_need_gives_none(self):
        self.assertIsNone(game(need=(5.0, 5.0), free=(5.0, 6.0)).opening_shortfall("school_founded"))


if __name__ == "__main__":
    unittest.main()
