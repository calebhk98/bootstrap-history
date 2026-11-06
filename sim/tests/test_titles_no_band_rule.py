"""The land-Gini band is sourced for some settings only: a setting with no row has no band."""
QUICK_TOPIC = True
import unittest

from sim.tests import titles_concentration


class NoLandBandTests(unittest.TestCase):
    def test_a_setting_with_no_sourced_row_has_no_band(self):
        self.assertIsNone(titles_concentration.band(titles_concentration.LANDHOLDERS_ONLY, ("no_such_setting",)))


if __name__ == "__main__":
    unittest.main()
