"""Plague mitigation: institutions protect while they run, knowledge lingers, the household is exposed to the national
epidemic, and national relief has no fixed ceiling. Each rule is called on a nation stub over the real arithmetic."""

QUICK_TOPIC = True

import unittest

from sim.engine.diffusion_rules import medical_relief
from sim.engine.society_diffusion import DiffusionMixin
from sim.tests.plague_exposure_stub import HISTORICAL_STAFF_LOSS, PlagueNation, bare, sanitised

COMPLIANCE_BASE = DiffusionMixin.MEDICAL_COMPLIANCE_BASE


class InstitutionVersusKnowledge(unittest.TestCase):

    def test_relief_orders_never_built_closed_running(self):
        never = PlagueNation().hazard_relief("staff_loss")[0]
        closed = PlagueNation(built=("plague_preparedness",)).hazard_relief("staff_loss")[0]
        running = PlagueNation(built=("plague_preparedness",), running=("plague_preparedness",)).hazard_relief("staff_loss")[0]
        self.assertEqual(never, 1.0)
        self.assertLess(closed, never)
        self.assertLess(running, closed)


class HouseholdIsExposedToTheCountry(unittest.TestCase):

    def test_household_loss_rises_with_national_prevalence(self):
        low_prevalence = sanitised(0.9).survivors_share()
        high_prevalence = sanitised(0.0).survivors_share()
        self.assertGreater(low_prevalence, high_prevalence)

    def test_household_mitigation_still_helps_at_equal_prevalence(self):
        self.assertGreater(sanitised(0.0).survivors_share(), bare(0.0).survivors_share())

    def test_the_loss_is_the_historical_rate_after_the_nation_then_after_the_household(self):
        nation = sanitised(0.25)
        exposure = nation.staff_loss_exposure(HISTORICAL_STAFF_LOSS)
        self.assertAlmostEqual(exposure["before_defences"], HISTORICAL_STAFF_LOSS * 0.75)
        self.assertAlmostEqual(exposure["loss"], exposure["before_defences"] * exposure["relief"])


class NationalRelief(unittest.TestCase):

    def test_full_coverage_exceeds_the_old_fixed_cap(self):
        self.assertFalse(hasattr(DiffusionMixin, "MEDICAL_DIFFUSION_RELIEF_CAP"))
        self.assertGreater(medical_relief(1.0, COMPLIANCE_BASE, 1.0), 0.85)

    def test_weak_state_leaves_a_residual_through_compliance(self):
        self.assertLess(medical_relief(1.0, COMPLIANCE_BASE, 0.0), medical_relief(1.0, COMPLIANCE_BASE, 1.0))

    def test_no_coverage_gives_no_relief_however_strong_the_state(self):
        self.assertEqual(medical_relief(0.0, COMPLIANCE_BASE, 1.0), 0.0)


if __name__ == "__main__":
    unittest.main()
