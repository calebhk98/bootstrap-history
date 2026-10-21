"""The concentration measures: top-decile share and Gini over holders' hectares."""

QUICK_TOPIC = True

import unittest

from sim.economy import titles_concentration


class MeasureTests(unittest.TestCase):
    def test_equal_holdings_have_no_inequality(self):
        self.assertAlmostEqual(titles_concentration.gini([5.0] * 10), 0.0)
        self.assertAlmostEqual(titles_concentration.top_decile_share([5.0] * 10), 0.1)

    def test_one_holder_with_everything_is_total_concentration(self):
        holdings = [0.0] * 9 + [100.0]
        self.assertAlmostEqual(titles_concentration.top_decile_share(holdings), 1.0)
        self.assertAlmostEqual(titles_concentration.gini(holdings), 0.9)

    def test_no_land_reads_as_zero(self):
        self.assertEqual(titles_concentration.gini([0.0, 0.0]), 0.0)
        self.assertEqual(titles_concentration.top_decile_share([]), 0.0)


class SourcedBandTests(unittest.TestCase):
    def test_the_band_is_the_hull_of_the_sourced_rows_for_the_denominator(self):
        low, high = titles_concentration.band(titles_concentration.LANDHOLDERS_ONLY)
        self.assertAlmostEqual(low, 0.374)       # Kerkeosiris, Scheidel 2019
        self.assertAlmostEqual(high, 0.758)      # Antinoopolis, Scheidel 2019
        self.assertEqual(titles_concentration.band(titles_concentration.LANDLESS_COUNTED), (0.65, 0.82))

    def test_counting_the_landless_gives_a_higher_figure_than_leaving_them_out(self):
        holdings = [0.0, 0.0, 2.0, 4.0, 6.0]
        by_denominator = titles_concentration.gini_by_denominator(holdings)
        self.assertGreater(by_denominator[titles_concentration.LANDLESS_COUNTED],
                           by_denominator[titles_concentration.LANDHOLDERS_ONLY])
        self.assertAlmostEqual(by_denominator[titles_concentration.LANDHOLDERS_ONLY], titles_concentration.gini([2.0, 4.0, 6.0]))

    def test_no_row_is_for_han_china_or_the_mexica(self):
        settings = {row.setting for row in titles_concentration.LAND_GINI_SOURCED}
        for civilisation in titles_concentration.NO_LAND_BAND:
            self.assertFalse(any(civilisation in setting for setting in settings))


if __name__ == "__main__":
    unittest.main()
