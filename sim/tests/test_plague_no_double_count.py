"""Plague mitigation does not double-count: a household's own defence applies only to the part of the country that has
not already adopted it, so the nation's relief and the household's never add past the whole."""

QUICK_TOPIC = True

import unittest

from sim.tests.plague_exposure_stub import HISTORICAL_STAFF_LOSS, SANITATION_SHARE, bare, sanitised


def household_relief(national_relief):
    """Staff the household's own sanitation saves, as a share of its staff, at this national adoption."""
    return sanitised(national_relief).survivors_share() - bare(national_relief).survivors_share()


class NoDoubleCountMitigation(unittest.TestCase):

    def test_full_national_coverage_household_relief_adds_nothing(self):
        self.assertAlmostEqual(sanitised(1.0).survivors_share(), bare(1.0).survivors_share(), places=9)
        self.assertEqual(sanitised(1.0).staff_loss_exposure(HISTORICAL_STAFF_LOSS)["relief"], 1.0)

    def test_zero_national_coverage_household_gets_full_relief(self):
        self.assertGreater(sanitised(0.0).survivors_share(), bare(0.0).survivors_share() * 1.1)
        self.assertAlmostEqual(sanitised(0.0).staff_loss_exposure(HISTORICAL_STAFF_LOSS)["relief"], 1.0 - SANITATION_SHARE)

    def test_survivors_rise_with_national_coverage_and_none_are_lost_at_full_coverage(self):
        full, half, zero = (sanitised(coverage).survivors_share() for coverage in (1.0, 0.5, 0.0))
        self.assertGreater(full, half)
        self.assertGreater(half, zero)
        self.assertEqual(full, 1.0)

    def test_household_relief_falls_as_national_coverage_rises(self):
        reliefs = [household_relief(coverage) for coverage in (0.0, 0.2, 0.5, 0.8, 1.0)]
        self.assertEqual(reliefs, sorted(reliefs, reverse=True))
        self.assertAlmostEqual(reliefs[-1], 0.0, places=9)

    def test_at_high_national_coverage_the_household_relief_is_small_and_at_low_it_is_substantial(self):
        maximum = household_relief(0.0)
        self.assertLess(household_relief(0.8), maximum * 0.3)
        self.assertGreater(household_relief(0.2), maximum * 0.5)


if __name__ == "__main__":
    unittest.main()
