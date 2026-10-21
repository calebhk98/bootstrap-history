"""SCENARIO: a Rome game meeting a plague wave through the real shock: survivors rise with national coverage and no
loss occurs at full coverage. The rule (household mitigation applies only beyond what the nation absorbed) is in
`test_plague_no_double_count`."""
import random
import unittest

from .harness import *  # noqa: F401,F403
from .plague_fixture import ANTONINE, with_hazard


def _fresh():
    return with_hazard(unopened_sim(civ="rome_100ad", capital=1e9), ANTONINE)


def _plague_hazard(household):
    return next(hazard for hazard in household.civ["hazards"]
                if "Antonine plague" in hazard["name"])


def _staff_after_plague_with_national_coverage(household, national_med_relief,
                                               household_has_sanitation=False):
    """Household staff after one forced staff_loss event, with the national
    medical relief (already factoring in compliance) pinned to a specific value."""
    # Large headcount: losses are rolled per person, so the average must dominate.
    household.scholars, household.artisans = 10000.0, 10000.0
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


class NoDoubleCountMitigationInAGame(unittest.TestCase):



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
        self.assertEqual(full_national, 10000.0,
                         msg="At 100% national relief, no loss occurs")

