"""Plague mitigation: institutions protect while they run, knowledge
lingers, the household is exposed to the national epidemic, and national
relief has no fixed ceiling."""
import random
import unittest

from .harness import *  # noqa: F401,F403

_MEDICAL_NODES = ("germ_theory", "med_quarantine_sanitation", "md2_vaccine_plague")


def _fresh():
    return sim(civ="rome_100ad", capital=1e9)


def _plague_hazard(household):
    return next(hazard for hazard in household.civ["hazards"]
                if "Antonine plague" in hazard["name"])


def _staff_after_plague(household, national_relief):
    """Household staff after one forced staff_loss event, with the national
    relief pinned so only the exposure differs between calls."""
    household.scholars, household.artisans = 100.0, 100.0
    household.medical_diffusion_relief = lambda: national_relief
    household.STAFF_LOSS_HAZARD_ANNUAL_CHANCE = 2.0
    household.rng = random.Random(3)
    hazard = _plague_hazard(household)
    household._shock_staff_loss(hazard, hazard["years"][0])
    return household.scholars


class InstitutionVersusKnowledge(unittest.TestCase):

    def test_relief_orders_never_built_closed_running(self):
        never = _fresh().hazard_relief("staff_loss")[0]
        closed = _fresh()
        closed.done.add("plague_preparedness")
        closed._done_changed()
        running = _fresh()
        running.done.add("plague_preparedness")
        running.operating.add("plague_preparedness")
        running._done_changed()
        closed_mult = closed.hazard_relief("staff_loss")[0]
        running_mult = running.hazard_relief("staff_loss")[0]
        self.assertLess(closed_mult, never)
        self.assertLess(running_mult, closed_mult)

    def test_pure_knowledge_is_not_switched_off(self):
        household = _fresh()
        household.done.add("germ_theory")
        household._done_changed()
        self.assertFalse(household.is_venture("germ_theory"))
        self.assertLess(household.hazard_relief("staff_loss")[0], 1.0)


class HouseholdIsExposedToTheCountry(unittest.TestCase):

    def test_household_loss_rises_with_national_prevalence(self):
        household_a, household_b = _fresh(), _fresh()
        for household in (household_a, household_b):
            household.done.add("sanitation_antisepsis")
            household.operating.add("sanitation_antisepsis")
            household._done_changed()
        low_prevalence = _staff_after_plague(household_a, 0.9)
        high_prevalence = _staff_after_plague(household_b, 0.0)
        self.assertGreater(low_prevalence, high_prevalence)

    def test_household_mitigation_still_helps_at_equal_prevalence(self):
        bare, protected = _fresh(), _fresh()
        protected.done.add("sanitation_antisepsis")
        protected.operating.add("sanitation_antisepsis")
        protected._done_changed()
        self.assertGreater(_staff_after_plague(protected, 0.0),
                           _staff_after_plague(bare, 0.0))


class NationalRelief(unittest.TestCase):

    def test_full_coverage_exceeds_the_old_fixed_cap(self):
        nation = _fresh()
        nation.state_capacity = 1.0
        nation.medical_diffusion_index = lambda: 1.0
        self.assertFalse(hasattr(nation, "MEDICAL_DIFFUSION_RELIEF_CAP"))
        self.assertGreater(nation.medical_diffusion_relief(), 0.85)

    def test_weak_state_leaves_a_residual_through_compliance(self):
        weak, strong = _fresh(), _fresh()
        weak.state_capacity, strong.state_capacity = 0.0, 1.0
        for nation in (weak, strong):
            nation.medical_diffusion_index = lambda: 1.0
        self.assertLess(weak.medical_diffusion_relief(),
                        strong.medical_diffusion_relief())

    def test_household_technique_diffuses_to_the_nation(self):
        nation = _fresh()
        for node_id in _MEDICAL_NODES:
            nation.done.add(node_id)
        year = nation.year
        reliefs = []
        for age in (0, 50, 400):
            nation.done_year = {node_id: year - age for node_id in _MEDICAL_NODES}
            reliefs.append(nation.medical_diffusion_relief())
        self.assertEqual(reliefs[0], 0.0)
        self.assertLess(reliefs[0], reliefs[1])
        self.assertLess(reliefs[1], reliefs[2])
