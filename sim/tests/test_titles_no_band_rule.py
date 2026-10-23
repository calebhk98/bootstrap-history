"""The land-Gini band is sourced for some civilisations only: none is given for Han China or the Mexica."""
QUICK_TOPIC = True
import unittest

from sim.economy import titles_concentration


class NoLandBandTests(unittest.TestCase):
    def test_han_china_and_the_mexica_have_no_band(self):
        self.assertEqual(titles_concentration.NO_LAND_BAND, ("han_china", "mexica"))
        self.assertIsNone(titles_concentration.band(titles_concentration.LANDHOLDERS_ONLY, ("han_china", "mexica")))


if __name__ == "__main__":
    unittest.main()
