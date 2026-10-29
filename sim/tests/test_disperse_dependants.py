"""`disperse_dependants` (the workforce module's handler of `DisperseDependants`): an insolvent household's freedmen leave and its
artisans fall by a share down to a floor; a count already below the floor stays (a dispersal never hires)."""
import unittest

from sim.tests import module_harness
from sim.workforce.api import DisperseDependants
from sim.workforce.module import Workforce
from sim.workforce.state import WorkforceSeat

QUICK_TOPIC = True


def dispersed(artisans, floor, retention):
    seat = WorkforceSeat(artisans=artisans, freedmen=4)
    module_harness.build(Workforce, seat=seat).disperse_dependants(DisperseDependants(floor, retention))
    return seat


class DisperseDependantsTests(unittest.TestCase):

    def test_the_artisans_fall_by_the_share_and_the_freedmen_leave(self):
        seat = dispersed(10.0, 3.0, 0.5)
        self.assertEqual((seat.artisans, seat.freedmen), (5.0, 0))

    def test_the_artisans_stop_falling_at_the_floor(self):
        self.assertEqual(dispersed(4.0, 3.0, 0.5).artisans, 3.0)

    def test_artisans_already_below_the_floor_stay_as_they_are(self):
        self.assertEqual(dispersed(1.0, 3.0, 0.5).artisans, 1.0)


if __name__ == "__main__":
    unittest.main()
