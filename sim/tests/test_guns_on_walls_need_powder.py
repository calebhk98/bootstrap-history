"""A defence credited to guns needs the powder works running (Complaints/249).

A node's `hazard_counters` entry may carry `requires_running`: node ids that
must themselves be running for the counter to count.
"""
import unittest

from .harness import *  # noqa: F401,F403

ARTILLERY = "mil_artillery_piece"
POWDER = "gunpowder"
GUNS_LABEL = "guns on the walls"


def _household(powder_running):
    household = sim(civ="rome_100ad", capital=1e9)
    household.done.update({ARTILLERY, POWDER})
    if powder_running:
        household.operating.add(POWDER)
    household._done_changed()
    return household


class GunsOnWallsNeedPowder(unittest.TestCase):

    def test_artillery_counter_declares_the_powder_it_needs(self):
        counters = NODES[ARTILLERY]["mechanics"]["hazard_counters"]
        guns = [counter for counter in counters if counter["label"] == GUNS_LABEL]
        self.assertEqual(guns[0].get("requires_running"), [POWDER])

    def test_guns_lapse_while_the_powder_works_is_closed(self):
        _mult, why = _household(powder_running=False).hazard_relief("sack_chance")
        guns = [item for item in why if item.startswith(GUNS_LABEL)]
        self.assertTrue(guns and "lapsed" in guns[0], why)

    def test_closing_the_powder_works_weakens_the_defence(self):
        closed = _household(powder_running=False).hazard_relief("sack_chance")[0]
        running = _household(powder_running=True).hazard_relief("sack_chance")[0]
        self.assertGreater(closed, running)

    def test_guns_count_while_the_powder_works_runs(self):
        _mult, why = _household(powder_running=True).hazard_relief("sack_chance")
        guns = [item for item in why if item.startswith(GUNS_LABEL)]
        self.assertTrue(guns and "lapsed" not in guns[0], why)


if __name__ == "__main__":
    unittest.main()
