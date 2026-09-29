"""Plague mitigation should not double-count: household mitigation applies
only to the portion the nation has not already absorbed."""
import random
import unittest

from .harness import *  # noqa: F401,F403


def _fresh():
    return sim(civ="rome_100ad", capital=1e9)


def _plague_hazard(household):
    return next(hazard for hazard in household.civ["hazards"]
                if "Antonine plague" in hazard["name"])


def _staff_after_plague_with_national_coverage(household, national_med_relief,
                                               household_has_sanitation=False):
    """Household staff after one forced staff_loss event, with the national
    medical relief (already factoring in compliance) pinned to a specific value."""
    household.scholars, household.artisans = 100.0, 100.0
    if household_has_sanitation:
        household.done.add("sanitation_antisepsis")
        household.operating.add("sanitation_antisepsis")
        household._done_changed()
    household.medical_diffusion_relief = lambda: national_med_relief
    household.civ_diffusion = lambda node_id: national_med_relief
    household.STAFF_LOSS_HAZARD_ANNUAL_CHANCE = 2.0
    household.rng = random.Random(3)
    hazard = _plague_hazard(household)
    household._shock_staff_loss(hazard, hazard["years"][0])
    return household.scholars


class NoDoubleCountMitigation(unittest.TestCase):

    def test_full_national_coverage_household_relief_adds_nothing(self):
        """When the nation has full medical relief (1.0), the household's
        own sanitation mitigation should add nothing beyond that."""
        no_household_mitigation = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=1.0, household_has_sanitation=False)
        with_household_mitigation = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=1.0, household_has_sanitation=True)
        self.assertAlmostEqual(no_household_mitigation, with_household_mitigation, places=5,
                               msg="At full national coverage, household mitigation should provide no extra relief")

    def test_zero_national_coverage_household_gets_full_relief(self):
        """When the nation has no medical relief (0.0), the household
        should get the full benefit of its mitigation."""
        no_mitigation = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=0.0, household_has_sanitation=False)
        with_mitigation = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=0.0, household_has_sanitation=True)
        self.assertGreater(with_mitigation, no_mitigation,
                           msg="At zero national coverage, household should benefit fully from mitigation")
        ratio = with_mitigation / no_mitigation if no_mitigation > 0 else 1.0
        self.assertGreater(ratio, 1.1,
                           msg="Household mitigation should provide meaningful relief when nation has none")

    def test_partial_national_coverage_household_scaled_relief(self):
        """With 50% national relief, household's mitigation benefit should
        scale down compared to zero national relief, but still provide benefit.
        Survivors should follow: full_national > half_national > zero_national."""
        full_national = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=1.0, household_has_sanitation=True)
        zero_national = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=0.0, household_has_sanitation=True)
        half_national = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=0.5, household_has_sanitation=True)
        self.assertGreater(full_national, half_national,
                           msg="Full national relief should lead to more survivors than half")
        self.assertGreater(half_national, zero_national,
                           msg="Half national relief should lead to more survivors than none")
        self.assertEqual(full_national, 100.0,
                         msg="At 100% national relief, no loss occurs")

    def test_household_relief_scales_with_national_coverage(self):
        """Household relief should scale approximately linearly with
        (1 - national_relief): at 80% national relief, household should
        only get about 20% of its maximum relief contribution."""
        full_national = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=1.0, household_has_sanitation=True)
        zero_national = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=0.0, household_has_sanitation=True)
        high_national = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=0.8, household_has_sanitation=True)
        low_national = _staff_after_plague_with_national_coverage(
            _fresh(), national_med_relief=0.2, household_has_sanitation=True)
        max_relief = zero_national - full_national
        high_relief = high_national - full_national
        low_relief = low_national - full_national
        if max_relief > 0.1:
            self.assertLess(high_relief, low_relief,
                             msg="Household relief should be smaller at higher national coverage")
            self.assertLess(high_relief, max_relief * 0.3,
                             msg="At 80% national coverage, household relief should be small")
            self.assertGreater(low_relief, max_relief * 0.5,
                               msg="At 20% national coverage, household relief should be substantial")
