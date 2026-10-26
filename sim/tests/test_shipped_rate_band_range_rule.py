"""The rates the opening's price solves are shipped for: bounded, distinct, banded, within the ceiling, covering nil
up to the start, and the nearest first. The rule is `banded_rates`, called on starting rates; how the solves are
replayed at those rates is test_shipped_rate_band_replay_rule."""

QUICK_TOPIC = True

import unittest

from sim.prices import prices

from sim.engine import shipped_rate_bands
from sim.world import capital_market


class BandRangeTests(unittest.TestCase):
    def test_bands_are_bounded_distinct_banded_and_not_above_the_ceiling(self):
        for starting_rate in (0.05, 0.1, 0.12, 0.2):
            rates = shipped_rate_bands.banded_rates(starting_rate)
            self.assertLessEqual(len(rates), shipped_rate_bands.MAX_BANDS)
            self.assertEqual(len(set(rates)), len(rates))
            self.assertNotIn(starting_rate, rates)
            for rate in rates:
                self.assertGreaterEqual(rate, 0.0)
                self.assertLessEqual(rate, starting_rate * capital_market.RATE_CEILING_SHARE)
                self.assertEqual(prices.band_interest_rate(rate, starting_rate), rate)

    def test_every_band_from_nil_to_the_start_is_covered_and_the_nearest_come_first(self):
        starting_rate = 0.12
        rates = shipped_rate_bands.banded_rates(starting_rate)
        self.assertIn(0.0, rates)
        self.assertEqual(set(rates[:2]), {prices.band_interest_rate(starting_rate + prices.INTEREST_RATE_BAND, starting_rate),
                                          prices.band_interest_rate(starting_rate - prices.INTEREST_RATE_BAND, starting_rate)})


if __name__ == "__main__":
    unittest.main()
